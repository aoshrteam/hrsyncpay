# apps/payroll/calculations.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from calendar import monthrange
from django.utils import timezone
from apps.employees.models import EmployeeAssignment
from apps.loans.models import EmployeeLoan, LoanDeduction  # ✅ Add LoanDeduction import
from apps.statutory.models import StatutorySettings, ProfessionalTaxSlab


class SalaryCalculator:
    """Complete Salary Calculation Engine"""

    def __init__(self, employee, assignment, month_year, attendance_data):
        self.employee = employee
        self.assignment = assignment
        self.month_year = month_year
        self.attendance = attendance_data
        self.days_in_month = self._get_days_in_month(month_year)
        self.settings = StatutorySettings.objects.first()

    def _get_days_in_month(self, month_year):
        """Get total days in month"""
        return monthrange(month_year.year, month_year.month)[1]

    def calculate_basic(self):
        """Calculate Basic Salary based on method"""
        method = self.assignment.salary_method
        monthly_basic = self.assignment.monthly_basic or 0
        days_present = self.attendance.get('days_present', 0) if self.attendance else 0
        per_day_rate = self.assignment.per_day_rate or 0
        rate_per_unit = self.assignment.rate_per_unit or 0
        production_units = self.attendance.get('production_units', 0) if self.attendance else 0

        if method == 'CALENDAR_MONTH':
            basic = (monthly_basic / Decimal(str(self.days_in_month))) * Decimal(str(days_present))

        elif method == '26_DAYS_MONTH':
            basic = (monthly_basic / Decimal(26)) * Decimal(str(days_present))

        elif method == 'PER_DAY':
            basic = per_day_rate * Decimal(str(days_present))

        elif method == 'PRODUCTION':
            basic = rate_per_unit * Decimal(str(production_units))

        else:
            basic = monthly_basic

        return Decimal(basic).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_allowances(self):
        """Calculate allowances"""
        return {
            'allowance': self.assignment.special_allowance or 0,
            'incentive': 0,  # Can be added separately
            'conveyance': self.assignment.conveyance_allowance or 0,
            'overtime': self._calculate_overtime(),
            'other_earnings': self.assignment.other_allowance or 0,
        }

    def _calculate_overtime(self):
        """Calculate overtime amount"""
        overtime_hours = self.attendance.get('overtime_hours', 0) if self.attendance else 0
        per_day_rate = self.assignment.per_day_rate or 0

        if per_day_rate > 0:
            per_hour_rate = per_day_rate / Decimal(8)
            overtime_rate = per_hour_rate * Decimal('1.5')
            overtime_amount = overtime_rate * Decimal(str(overtime_hours))
        else:
            overtime_amount = Decimal(0)

        return Decimal(overtime_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # apps/payroll/calculations.py - Update PF calculation

    def calculate_pf(self, basic_salary):
        """Calculate PF and EPS - Uses Assignment EPS settings"""
        if not self.settings:
            return {'employee': 0, 'employer': 0, 'eps_employer': 0, 'admin_charges': 0, 'edlis_charges': 0,
                    'pf_basic': 0}

        pf_cap = self.assignment.pf_cap

        if pf_cap == 'NOT_APPLICABLE' or not self.settings.pf_applicable:
            return {'employee': 0, 'employer': 0, 'eps_employer': 0, 'admin_charges': 0, 'edlis_charges': 0,
                    'pf_basic': 0}

        # Determine PF limit
        if pf_cap == 'CAPPED_15000':
            pf_limit = Decimal(15000)
        elif pf_cap == 'CAPPED_18000':
            pf_limit = Decimal(18000)
        elif pf_cap == 'FULL':
            pf_limit = Decimal('999999')
        else:
            pf_limit = Decimal(15000)

        pf_basic = min(basic_salary, pf_limit)

        # PF Rates
        if self.employee.pf_override:
            employee_rate = self.employee.pf_employee_rate / 100
            employer_rate = self.employee.pf_employer_rate / 100
        else:
            employee_rate = self.settings.pf_employee_rate / 100
            employer_rate = self.settings.pf_employer_rate / 100

        # ✅ EPS Rates from Assignment (if applicable)
        if self.assignment.eps_applicable:
            eps_rate = self.assignment.eps_employer_rate / 100
            eps_limit = self.assignment.eps_limit
            eps_basic = min(pf_basic, eps_limit)
        else:
            eps_rate = Decimal(0)
            eps_basic = Decimal(0)

        admin_rate = Decimal('0.005')  # 0.50%
        edlis_rate = Decimal('0.005')  # 0.50%

        pf_employee = (pf_basic * employee_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        pf_employer = (pf_basic * employer_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        eps_employer = (eps_basic * eps_rate).quantize(Decimal('0.01'),
                                                       rounding=ROUND_HALF_UP) if eps_rate > 0 else Decimal(0)
        admin_charges = (pf_basic * admin_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        edlis_charges = (pf_basic * edlis_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'employee': pf_employee,
            'employer': pf_employer,
            'eps_employer': eps_employer,
            'admin_charges': admin_charges,
            'edlis_charges': edlis_charges,
            'pf_basic': pf_basic,
        }

    def calculate_esi(self, gross_earnings):
        """Calculate ESI"""
        if not self.settings or not self.settings.esi_applicable:
            return {'employee': 0, 'employer': 0}

        esi_rule = self.assignment.esi_rule

        if esi_rule == 'EXEMPT':
            return {'employee': 0, 'employer': 0}

        esi_limit = self.settings.esi_limit or Decimal(21000)

        if esi_rule == 'AUTO' and gross_earnings > esi_limit:
            return {'employee': 0, 'employer': 0}

        # ESI Rates
        employee_rate = self.settings.esi_employee_rate / Decimal(100)
        employer_rate = self.settings.esi_employer_rate / Decimal(100)

        esi_employee = (gross_earnings * employee_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        esi_employer = (gross_earnings * employer_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {'employee': esi_employee, 'employer': esi_employer}

    def calculate_professional_tax(self, gross_earnings):
        """Calculate Professional Tax"""
        if not self.settings or not self.settings.pt_applicable:
            return 0

        state = self.settings.pt_state
        slabs = ProfessionalTaxSlab.objects.filter(state=state, is_active=True).order_by('min_amount')

        if not slabs:
            return 0

        pt_amount = Decimal(0)
        for slab in slabs:
            if slab.min_amount <= gross_earnings:
                if slab.max_amount and gross_earnings <= slab.max_amount:
                    pt_amount = slab.tax_amount
                    break
                elif not slab.max_amount:
                    pt_amount = slab.tax_amount
                    break

        return Decimal(pt_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_tds(self, gross_earnings):
        """Calculate TDS"""
        if not self.settings or not self.settings.tds_applicable:
            return 0

        if self.settings.tds_type == 'PERCENTAGE':
            tds_amount = gross_earnings * (self.settings.tds_rate / Decimal(100))
        else:
            tds_amount = self.settings.tds_rate

        return Decimal(tds_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_loan_deductions(self):
        """Calculate all loan deductions for this month"""
        deductions = {}
        total = Decimal(0)

        active_loans = EmployeeLoan.objects.filter(
            employee=self.employee,
            status='ACTIVE',
            first_deduction_date__lte=self.month_year
        )

        for loan in active_loans:
            # Check if installment already deducted for this month
            existing_deduction = LoanDeduction.objects.filter(
                employee_loan=loan,
                month_year=self.month_year,
                deducted=True
            ).exists()

            if not existing_deduction and loan.remaining_installments > 0:
                deduction_amount = loan.installment_amount

                # Calculate principal and interest (approx)
                principal_portion = deduction_amount * Decimal('0.8')
                interest_portion = deduction_amount * Decimal('0.2')

                # Create loan deduction record
                deduction = LoanDeduction.objects.create(
                    employee_loan=loan,
                    month_year=self.month_year,
                    installment_number=loan.paid_installments + 1,
                    amount=deduction_amount,
                    principal_amount=principal_portion,
                    interest_amount=interest_portion,
                    deducted=False
                )

                loan_type_name = loan.loan_type.name
                deductions[loan_type_name] = deductions.get(loan_type_name, 0) + deduction_amount
                total += deduction_amount

                # Update loan
                loan.paid_installments += 1
                loan.remaining_installments -= 1
                if loan.remaining_installments <= 0:
                    loan.status = 'CLOSED'
                    loan.last_deduction_date = timezone.now().date()
                loan.save()

        return {'details': deductions, 'total': total}

    def process(self):
        """Complete salary processing"""
        # Step 1: Calculate Basic
        basic = self.calculate_basic()

        # Step 2: Calculate Allowances
        allowances = self.calculate_allowances()

        # Step 3: Calculate Gross Earnings
        gross = basic + allowances['allowance'] + allowances['incentive'] + \
                allowances['conveyance'] + allowances['overtime'] + allowances['other_earnings']
        gross = Decimal(gross).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Step 4: Calculate PF
        pf = self.calculate_pf(basic)

        # Step 5: Calculate ESI
        esi = self.calculate_esi(gross)

        # Step 6: Calculate Professional Tax
        pt = self.calculate_professional_tax(gross)

        # Step 7: Calculate TDS
        tds = self.calculate_tds(gross)

        # Step 8: Calculate Loan Deductions
        loan_deductions = self.calculate_loan_deductions()

        # Step 9: Calculate Total Deductions
        total_deductions = pf['employee'] + esi['employee'] + pt + tds + loan_deductions['total']

        # Step 10: Calculate Net Pay
        net_pay = gross - total_deductions

        return {
            'basic_pay': basic,
            'allowance': allowances['allowance'],
            'incentive': allowances['incentive'],
            'conveyance': allowances['conveyance'],
            'overtime': allowances['overtime'],
            'other_earnings': allowances['other_earnings'],
            'gross_earnings': gross,
            'pf_basic': pf['pf_basic'],
            'pf_employee': pf['employee'],
            'pf_employer': pf['employer'],
            'eps_employer': pf['eps_employer'],
            'admin_charges': pf['admin_charges'],
            'edlis_charges': pf['edlis_charges'],
            'esi_employee': esi['employee'],
            'esi_employer': esi['employer'],
            'professional_tax': pt,
            'tds': tds,
            'loan_deductions': loan_deductions['details'],
            'loan_total': loan_deductions['total'],
            'total_deductions': total_deductions,
            'net_pay': net_pay,
        }