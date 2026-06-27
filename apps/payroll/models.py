# apps/payroll/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from apps.employees.models import Employee, EmployeeAssignment
from apps.clients.models import Client
from apps.loans.models import EmployeeLoan, LoanDeduction
from apps.statutory.models import StatutorySettings, ProfessionalTaxSlab, PFChallan, ESIChallan


class PayrollRun(models.Model):
    """Payroll Run - Master record for monthly payroll processing"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PROCESSING', 'Processing'),
        ('PROCESSED', 'Processed'),
        ('FINALIZED', 'Finalized'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Basic Info
    run_number = models.CharField(max_length=50, unique=True)
    month_year = models.DateField(help_text="First day of month")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True,
                               help_text="Leave blank for all clients")

    # Summary Totals
    total_employees = models.IntegerField(default=0)
    total_gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_net_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Statutory Totals
    total_pf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_eps_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_esi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_esi_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Audit
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                   related_name='created_payroll_runs')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.run_number} - {self.month_year.strftime('%B %Y')}"

    def save(self, *args, **kwargs):
        if not self.run_number:
            month_str = self.month_year.strftime('%Y%m') if self.month_year else timezone.now().strftime('%Y%m')
            last_run = PayrollRun.objects.filter(run_number__startswith=f'PR-{month_str}').order_by(
                '-run_number').first()
            if last_run:
                last_num = int(last_run.run_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.run_number = f"PR-{month_str}-{new_num:04d}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-month_year']
        unique_together = ['month_year', 'client']


class Payslip(models.Model):
    """Employee Payslip - Generated from Payroll Run"""

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    assignment = models.ForeignKey(EmployeeAssignment, on_delete=models.SET_NULL, null=True)

    # Earnings
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions - Statutory
    pf_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pf_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    eps_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pf_basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    edlis_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    esi_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esi_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tds = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions - Loans & Others
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Net Pay
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Loan Details (JSON)
    loan_details = models.JSONField(default=dict, blank=True)

    # Status
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)

    # PDF
    pdf_file = models.FileField(upload_to='payslips/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.payroll_run.month_year.strftime('%B %Y')}"

    def calculate_totals(self):
        """Calculate all totals for this payslip"""
        # Gross Earnings
        self.gross_earnings = (
                self.basic_pay + self.allowance + self.incentive +
                self.conveyance + self.overtime + self.other_earnings
        )

        # Total Deductions
        self.total_deductions = (
                self.pf_employee + self.esi_employee + self.professional_tax +
                self.tds + self.loan_deduction + self.advance_deduction +
                self.other_deductions
        )

        # Net Pay
        self.net_pay = self.gross_earnings - self.total_deductions

        return self

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['payroll_run', 'employee']
        ordering = ['employee__name']


# apps/payroll/models.py - Add these models at the end

class PaymentVoucher(models.Model):
    """Payment Voucher for Salary Disbursement"""

    PAYMENT_TYPE_CHOICES = [
        ('SALARY', 'Salary'),
        ('ALLOWANCE', 'Allowance'),
        ('INCENTIVE', 'Incentive'),
        ('BONUS', 'Bonus'),
        ('CONVEYANCE', 'Conveyance'),
        ('LOAN', 'Loan Recovery'),
        ('ADVANCE', 'Advance'),
        ('OTHER', 'Other'),
    ]

    PAYMENT_STATUS = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    voucher_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='SALARY')

    # Reference to Payroll Run
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, null=True, blank=True)

    # Summary Amounts
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Accounting References (Ledger IDs)
    payable_ledger_id = models.IntegerField(null=True, blank=True, help_text="Reference to accounting ledger for debit")
    bank_ledger_id = models.IntegerField(null=True, blank=True, help_text="Reference to accounting ledger for credit")

    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='DRAFT')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_payments')
    approved_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Accounting Voucher Reference
    accounting_voucher_id = models.CharField(max_length=50, blank=True, null=True)

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                   related_name='created_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PAY-{self.payment_date.strftime('%Y%m%d')}-{self.id}"

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            date_str = self.payment_date.strftime('%Y%m%d') if self.payment_date else timezone.now().strftime('%Y%m%d')
            last_payment = PaymentVoucher.objects.filter(voucher_number__startswith=f'PAY-{date_str}').order_by(
                '-id').first()
            if last_payment:
                last_num = int(last_payment.voucher_number.split('-')[-1]) if last_payment.voucher_number.split('-')[
                    -1].isdigit() else 0
                new_num = last_num + 1
            else:
                new_num = 1
            self.voucher_number = f"PAY-{date_str}-{new_num:04d}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-payment_date']


class PaymentVoucherDetail(models.Model):
    """Employee-wise Payment Details"""

    payment_voucher = models.ForeignKey(PaymentVoucher, on_delete=models.CASCADE, related_name='details')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE)
    payslip = models.ForeignKey(Payslip, on_delete=models.SET_NULL, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)

    # Reference to process voucher detail (for tracking)
    process_voucher_detail_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} - ₹{self.amount}"

    class Meta:
        ordering = ['employee__name']


# apps/payroll/models.py - Add this at the end

class EmployeeLedger(models.Model):
    """Employee-wise ledger maintained in payroll"""

    TRANSACTION_TYPE = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='ledger_entries')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Source reference
    source_type = models.CharField(max_length=50, blank=True)  # 'PAYROLL', 'PAYMENT', 'ADJUSTMENT'
    source_id = models.CharField(max_length=50, blank=True)

    # Month/Year for reporting
    month_year = models.DateField(help_text="First day of month")
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, null=True, blank=True)

    # Description
    description = models.CharField(max_length=200, blank=True)

    # Running balance
    running_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.transaction_type} - ₹{self.amount} - {self.transaction_date}"

    class Meta:
        ordering = ['employee', 'transaction_date', 'created_at']
        indexes = [
            models.Index(fields=['employee', 'transaction_date']),
            models.Index(fields=['employee', 'month_year']),
            models.Index(fields=['client', 'month_year']),
        ]