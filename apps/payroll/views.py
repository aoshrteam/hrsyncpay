# apps/payroll/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from decimal import Decimal

from .models import PayrollRun, Payslip, PaymentVoucher, PaymentVoucherDetail  # ✅ Add Payment models
from .calculations import SalaryCalculator
from .forms import PaymentSelectionForm  # ✅ Add this import
from apps.attendance.models import AttendanceVoucher, AttendanceDetail
from apps.employees.models import Employee, EmployeeAssignment
from apps.clients.models import Client
from apps.loans.models import EmployeeLoan, LoanDeduction
from apps.core.decorators import data_entry_or_admin_required

# Import from statutory
from apps.statutory.models import StatutorySettings
from apps.statutory.models import PFChallan
from apps.statutory.models import PFChallanDetail
from apps.statutory.models import ESIChallan


# ============================================
# PAYROLL RUN MANAGEMENT (Existing)
# ============================================

# apps/payroll/views.py - Update payroll_run_list

# apps/payroll/views.py

@login_required
def payroll_run_list(request):
    """Payroll Run List View"""
    runs = PayrollRun.objects.all().order_by('-month_year')

    # Filter by client
    client_id = request.GET.get('client')
    if client_id:
        runs = runs.filter(client_id=client_id)

    # Filter by status
    status = request.GET.get('status')
    if status:
        runs = runs.filter(status=status)

    # Pagination
    paginator = Paginator(runs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ✅ Debug - check if any run has id = None
    for run in page_obj:
        if not run.id:
            print(f"WARNING: Run {run.run_number} has no ID!")

    context = {
        'page_obj': page_obj,
        'clients': Client.objects.filter(is_active=True),
        'status_choices': PayrollRun.STATUS_CHOICES,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payroll Runs', 'active': True},
        ],
    }
    return render(request, 'payroll/run_list.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payroll_run_create(request):
    """Create New Payroll Run"""
    if request.method == 'POST':
        month_year = request.POST.get('month_year')
        client_id = request.POST.get('client')

        if not month_year:
            messages.error(request, 'Please select month and year.')
            return redirect('payroll:run_create')

        month_year = timezone.datetime.strptime(month_year, '%Y-%m').date()
        client = Client.objects.get(id=client_id) if client_id else None

        existing_run = PayrollRun.objects.filter(month_year=month_year, client=client).first()
        if existing_run:
            messages.warning(request, f'Payroll run already exists for {month_year.strftime("%B %Y")}!')
            return redirect('payroll:run_detail', pk=existing_run.pk)

        run = PayrollRun.objects.create(
            month_year=month_year,
            client=client,
            created_by=request.user,
            status='DRAFT'
        )

        messages.success(request, f'Payroll run {run.run_number} created successfully!')
        return redirect('payroll:run_process', pk=run.pk)

    context = {
        'clients': Client.objects.filter(is_active=True),
        'current_month': timezone.now().strftime('%Y-%m'),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payroll Runs', 'url': '/payroll/', 'active': False},
            {'name': 'Create', 'active': True},
        ],
    }
    return render(request, 'payroll/run_create.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payroll_run_process(request, pk):
    """Process Payroll Run"""
    run = get_object_or_404(PayrollRun, pk=pk)

    if run.status not in ['DRAFT', 'PROCESSING']:
        messages.warning(request, 'This payroll run is already processed or finalized.')
        return redirect('payroll:run_detail', pk=run.pk)

    if run.client:
        employees = Employee.objects.filter(
            assignments__client=run.client,
            assignments__is_current=True,
            is_active=True
        ).distinct()
    else:
        employees = Employee.objects.filter(is_active=True)

    if not employees.exists():
        messages.error(request, 'No employees found for this payroll run.')
        return redirect('payroll:run_detail', pk=run.pk)

    attendance_voucher = AttendanceVoucher.objects.filter(
        month_year=run.month_year,
        client=run.client
    ).first() if run.client else None

    processed_count = 0
    total_gross = Decimal(0)
    total_net = Decimal(0)
    total_pf_emp = Decimal(0)
    total_pf_empl = Decimal(0)
    total_esi_emp = Decimal(0)
    total_esi_empl = Decimal(0)
    total_pt = Decimal(0)
    total_tds = Decimal(0)
    total_loan = Decimal(0)

    for employee in employees:
        if run.client:
            assignment = employee.assignments.filter(client=run.client, is_current=True).first()
        else:
            assignment = employee.assignments.filter(is_current=True).first()

        if not assignment:
            continue

        attendance_data = None
        if attendance_voucher:
            attendance_detail = AttendanceDetail.objects.filter(
                attendance_voucher=attendance_voucher,
                employee=employee
            ).first()
            if attendance_detail:
                attendance_data = {
                    'days_present': attendance_detail.days_present,
                    'days_absent': attendance_detail.days_absent,
                    'days_leave': attendance_detail.days_leave,
                    'overtime_hours': attendance_detail.overtime_hours,
                    'production_units': attendance_detail.production_units,
                }

        calculator = SalaryCalculator(employee, assignment, run.month_year, attendance_data)
        result = calculator.process()

        payslip = Payslip.objects.create(
            payroll_run=run,
            employee=employee,
            assignment=assignment,
            basic_pay=result['basic_pay'],
            allowance=result['allowance'],
            incentive=result['incentive'],
            conveyance=result['conveyance'],
            overtime=result['overtime'],
            other_earnings=result['other_earnings'],
            gross_earnings=result['gross_earnings'],
            pf_basic=result['pf_basic'],
            pf_employee=result['pf_employee'],
            pf_employer=result['pf_employer'],
            eps_employer=result['eps_employer'],
            admin_charges=result['admin_charges'],
            edlis_charges=result['edlis_charges'],
            esi_employee=result['esi_employee'],
            esi_employer=result['esi_employer'],
            professional_tax=result['professional_tax'],
            tds=result['tds'],
            loan_deduction=result['loan_total'],
            loan_details=result['loan_deductions'],
            total_deductions=result['total_deductions'],
            net_pay=result['net_pay'],
        )

        processed_count += 1
        total_gross += result['gross_earnings']
        total_net += result['net_pay']
        total_pf_emp += result['pf_employee']
        total_pf_empl += result['pf_employer']
        total_esi_emp += result['esi_employee']
        total_esi_empl += result['esi_employer']
        total_pt += result['professional_tax']
        total_tds += result['tds']
        total_loan += result['loan_total']

    run.total_employees = processed_count
    run.total_gross_salary = total_gross
    run.total_net_payable = total_net
    run.total_pf_employee = total_pf_emp
    run.total_pf_employer = total_pf_empl
    run.total_esi_employee = total_esi_emp
    run.total_esi_employer = total_esi_empl
    run.total_professional_tax = total_pt
    run.total_tds = total_tds
    run.total_loan_deduction = total_loan
    run.status = 'PROCESSED'
    run.processed_at = timezone.now()
    run.save()

    messages.success(request, f'Payroll processed successfully! {processed_count} employees processed.')
    return redirect('payroll:run_detail', pk=run.pk)


@login_required
def payroll_run_detail(request, pk):
    """Payroll Run Detail View"""
    run = get_object_or_404(PayrollRun, pk=pk)
    payslips = run.payslips.all()

    context = {
        'run': run,
        'payslips': payslips,
        'total_employees': payslips.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payroll Runs', 'url': '/payroll/', 'active': False},
            {'name': run.run_number, 'active': True},
        ],
    }
    return render(request, 'payroll/run_detail.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payroll_run_finalize(request, pk):
    """Finalize Payroll Run"""
    run = get_object_or_404(PayrollRun, pk=pk)

    if run.status != 'PROCESSED':
        messages.warning(request, 'Only processed runs can be finalized.')
        return redirect('payroll:run_detail', pk=run.pk)

    run.status = 'FINALIZED'
    run.finalized_at = timezone.now()
    run.save()

    generate_pf_challan(run)
    generate_esi_challan(run)

    messages.success(request, f'Payroll run {run.run_number} finalized and challans generated!')
    return redirect('payroll:run_detail', pk=run.pk)


# ============================================
# CHALLAN GENERATION
# ============================================

def generate_pf_challan(payroll_run):
    """Generate PF Challan for payroll run"""
    month = payroll_run.month_year.strftime('%b').upper()
    year = payroll_run.month_year.year
    payslips = payroll_run.payslips.filter(pf_basic__gt=0)

    if not payslips.exists():
        return None

    challan, created = PFChallan.objects.get_or_create(
        month=month,
        year=year,
        defaults={
            'payroll_run_id': payroll_run.id,
            'total_employees': 0,
            'total_pf_basic': 0,
            'total_employee_share': 0,
            'total_employer_share': 0,
            'total_eps_share': 0,
            'total_admin_charges': 0,
            'total_edlis_charges': 0,
            'total_amount': 0,
            'generated': False,
        }
    )

    if created or not challan.generated:
        PFChallanDetail.objects.filter(challan=challan).delete()

        total_employees = 0
        total_pf_basic = Decimal(0)
        total_employee_share = Decimal(0)
        total_employer_share = Decimal(0)
        total_eps_share = Decimal(0)
        total_admin_charges = Decimal(0)
        total_edlis_charges = Decimal(0)

        for payslip in payslips:
            total_employees += 1
            total_pf_basic += payslip.pf_basic
            total_employee_share += payslip.pf_employee
            total_employer_share += payslip.pf_employer
            total_eps_share += payslip.eps_employer
            total_admin_charges += payslip.admin_charges
            total_edlis_charges += payslip.edlis_charges

            PFChallanDetail.objects.create(
                challan=challan,
                employee=payslip.employee,
                client=payslip.assignment.client if payslip.assignment else None,
                employee_name=payslip.employee.name,
                employee_code=payslip.employee.employee_code,
                assignment_code=payslip.assignment.assignment_code if payslip.assignment else '',
                pf_basic=payslip.pf_basic,
                employee_share=payslip.pf_employee,
                employer_share=payslip.pf_employer,
                eps_share=payslip.eps_employer,
            )

        challan.total_employees = total_employees
        challan.total_pf_basic = total_pf_basic
        challan.total_employee_share = total_employee_share
        challan.total_employer_share = total_employer_share
        challan.total_eps_share = total_eps_share
        challan.total_admin_charges = total_admin_charges
        challan.total_edlis_charges = total_edlis_charges
        challan.total_amount = (
                total_employee_share + total_employer_share +
                total_eps_share + total_admin_charges + total_edlis_charges
        )
        challan.generated = True
        challan.generated_at = timezone.now()
        challan.save()

    return challan


def generate_esi_challan(payroll_run):
    """Generate ESI Challan for payroll run"""
    month = payroll_run.month_year.strftime('%b').upper()
    year = payroll_run.month_year.year
    payslips = payroll_run.payslips.filter(esi_employee__gt=0)

    if not payslips.exists():
        return None

    challan, created = ESIChallan.objects.get_or_create(
        month=month,
        year=year,
        defaults={
            'payroll_run_id': payroll_run.id,
            'total_employee_share': 0,
            'total_employer_share': 0,
            'total_amount': 0,
            'generated': False,
        }
    )

    if created or not challan.generated:
        total_employee_share = Decimal(0)
        total_employer_share = Decimal(0)

        for payslip in payslips:
            total_employee_share += payslip.esi_employee
            total_employer_share += payslip.esi_employer

        challan.total_employee_share = total_employee_share
        challan.total_employer_share = total_employer_share
        challan.total_amount = total_employee_share + total_employer_share
        challan.generated = True
        challan.generated_at = timezone.now()
        challan.save()

    return challan


# ============================================
# PAYSLIP VIEWS
# ============================================

@login_required
def payslip_detail(request, pk):
    """View Payslip"""
    payslip = get_object_or_404(Payslip, pk=pk)

    context = {
        'payslip': payslip,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payroll Runs', 'url': '/payroll/', 'active': False},
            {'name': payslip.payroll_run.run_number, 'url': f'/payroll/{payslip.payroll_run.id}/', 'active': False},
            {'name': payslip.employee.name, 'active': True},
        ],
    }
    return render(request, 'payroll/payslip_detail.html', context)


@login_required
def payslip_pdf(request, pk):
    """Generate Payslip PDF"""
    payslip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll/payslip_pdf.html', {'payslip': payslip})


# ============================================
# PAYMENT VOUCHER VIEWS (New)
# ============================================

@login_required
def payment_voucher_list(request):
    """Payment Voucher List View"""
    vouchers = PaymentVoucher.objects.all().order_by('-payment_date')  # ✅ Now defined

    client_id = request.GET.get('client')
    if client_id:
        vouchers = vouchers.filter(client_id=client_id)

    status = request.GET.get('status')
    if status:
        vouchers = vouchers.filter(status=status)

    paginator = Paginator(vouchers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'clients': Client.objects.filter(is_active=True),
        'status_choices': PaymentVoucher.PAYMENT_STATUS,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payment Vouchers', 'active': True},
        ],
    }
    return render(request, 'payroll/payment_voucher_list.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payment_voucher_create(request):
    """Create Payment Voucher"""

    if request.method == 'POST':
        payroll_run_id = request.POST.get('payroll_run')
        if not payroll_run_id:
            messages.error(request, 'Please select a payroll run.')
            return redirect('payroll:payment_voucher_create')

        payroll_run = get_object_or_404(PayrollRun, id=payroll_run_id)

        form = PaymentSelectionForm(request.POST, payroll_run=payroll_run)  # ✅ Now defined
        if form.is_valid():
            selected_data = []
            total_amount = 0

            for key, value in form.cleaned_data.items():
                if key.startswith('select_') and value:
                    employee_id = key.split('_')[1]
                    amount_key = f'emp_{employee_id}'
                    amount = form.cleaned_data.get(amount_key, 0)
                    if amount > 0:
                        selected_data.append({
                            'employee_id': employee_id,
                            'amount': amount,
                        })
                        total_amount += amount

            if not selected_data:
                messages.error(request, 'Please select at least one employee.')
                return redirect('payroll:payment_voucher_create')

            request.session['payment_selected_data'] = selected_data
            request.session['payment_payroll_run_id'] = payroll_run.id
            request.session['payment_total_amount'] = float(total_amount)

            return redirect('payroll:payment_voucher_confirm')

    payroll_run_id = request.GET.get('payroll_run')
    payroll_run = None
    if payroll_run_id:
        payroll_run = get_object_or_404(PayrollRun, id=payroll_run_id)

    payroll_runs = PayrollRun.objects.filter(status__in=['PROCESSED', 'FINALIZED']).order_by('-month_year')

    payslips = []
    if payroll_run:
        payslips = payroll_run.payslips.filter(paid=False).select_related('employee')

    context = {
        'payroll_runs': payroll_runs,
        'selected_payroll_run': payroll_run,
        'payslips': payslips,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payment Vouchers', 'url': '/payroll/payments/', 'active': False},
            {'name': 'Create Payment', 'active': True},
        ],
    }
    return render(request, 'payroll/payment_voucher_create.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payment_voucher_confirm(request):
    """Confirm Payment Voucher"""

    selected_data = request.session.get('payment_selected_data', [])
    payroll_run_id = request.session.get('payment_payroll_run_id')
    total_amount = request.session.get('payment_total_amount', 0)

    if not selected_data or not payroll_run_id:
        messages.error(request, 'No payment data found. Please start over.')
        return redirect('payroll:payment_voucher_create')

    payroll_run = get_object_or_404(PayrollRun, id=payroll_run_id)

    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')
        payment_date = request.POST.get('payment_date')
        notes = request.POST.get('notes', '')

        if not payment_type or not payment_date:
            messages.error(request, 'Please fill all required fields.')
            return redirect('payroll:payment_voucher_confirm')

        voucher = PaymentVoucher.objects.create(  # ✅ Now defined
            payment_date=payment_date,
            payment_type=payment_type,
            payroll_run=payroll_run,
            client=payroll_run.client,
            total_amount=total_amount,
            notes=notes,
            created_by=request.user,
            status='DRAFT'
        )

        for data in selected_data:
            employee = get_object_or_404(Employee, id=data['employee_id'])
            payslip = Payslip.objects.filter(payroll_run=payroll_run, employee=employee).first()

            PaymentVoucherDetail.objects.create(  # ✅ Now defined
                payment_voucher=voucher,
                employee=employee,
                payslip=payslip,
                amount=data['amount'],
                description=f"Payment for {payroll_run.month_year.strftime('%B %Y')}"
            )

            if payslip and data['amount'] >= payslip.net_pay:
                payslip.paid = True
                payslip.paid_date = payment_date
                payslip.save()

        request.session.pop('payment_selected_data', None)
        request.session.pop('payment_payroll_run_id', None)
        request.session.pop('payment_total_amount', None)

        messages.success(request, f'Payment Voucher {voucher.voucher_number} created successfully!')
        return redirect('payroll:payment_voucher_detail', pk=voucher.pk)

    employees_data = []
    for data in selected_data:
        employee = Employee.objects.get(id=data['employee_id'])
        payslip = Payslip.objects.filter(payroll_run=payroll_run, employee=employee).first()
        employees_data.append({
            'employee': employee,
            'amount': data['amount'],
            'payslip': payslip,
        })

    context = {
        'employees_data': employees_data,
        'payroll_run': payroll_run,
        'total_amount': total_amount,
        'payment_types': PaymentVoucher.PAYMENT_TYPE_CHOICES,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payment Vouchers', 'url': '/payroll/payments/', 'active': False},
            {'name': 'Confirm Payment', 'active': True},
        ],
    }
    return render(request, 'payroll/payment_voucher_confirm.html', context)


@login_required
def payment_voucher_detail(request, pk):
    """Payment Voucher Detail View"""
    voucher = get_object_or_404(PaymentVoucher, pk=pk)  # ✅ Now defined
    details = voucher.details.all()

    context = {
        'voucher': voucher,
        'details': details,
        'total_employees': details.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payment Vouchers', 'url': '/payroll/payments/', 'active': False},
            {'name': voucher.voucher_number, 'active': True},
        ],
    }
    return render(request, 'payroll/payment_voucher_detail.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payment_voucher_approve(request, pk):
    """Approve Payment Voucher"""
    voucher = get_object_or_404(PaymentVoucher, pk=pk)  # ✅ Now defined

    if voucher.status != 'DRAFT':
        messages.warning(request, 'Only draft vouchers can be approved.')
        return redirect('payroll:payment_voucher_detail', pk=voucher.pk)

    voucher.status = 'PAID'
    voucher.approved_by = request.user
    voucher.approved_date = timezone.now()
    voucher.paid_at = timezone.now()
    voucher.save()

    for detail in voucher.details.all():
        if detail.payslip:
            detail.payslip.paid = True
            detail.payslip.paid_date = voucher.payment_date
            detail.payslip.save()

    messages.success(request, f'Payment Voucher {voucher.voucher_number} approved and marked as paid!')
    return redirect('payroll:payment_voucher_detail', pk=voucher.pk)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def payment_voucher_cancel(request, pk):
    """Cancel Payment Voucher"""
    voucher = get_object_or_404(PaymentVoucher, pk=pk)  # ✅ Now defined

    if voucher.status == 'PAID':
        messages.error(request, 'Cannot cancel a paid voucher.')
        return redirect('payroll:payment_voucher_detail', pk=voucher.pk)

    if request.method == 'POST':
        voucher.status = 'CANCELLED'
        voucher.save()
        messages.success(request, f'Payment Voucher {voucher.voucher_number} cancelled.')
        return redirect('payroll:payment_voucher_list')

    context = {
        'voucher': voucher,
    }
    return render(request, 'payroll/payment_voucher_cancel.html', context)


# apps/payroll/views.py

@login_required
def payslip_pdf(request, pk):
    """Generate Payslip PDF View"""
    payslip = get_object_or_404(Payslip, pk=pk)

    # Return HTML view (PDF will be generated by browser print)
    return render(request, 'payroll/payslip_pdf.html', {'payslip': payslip})


# apps/payroll/views.py - Add this view

@login_required
@data_entry_or_admin_required
@transaction.atomic
def payroll_run_delete(request, pk):
    """Delete Payroll Run"""
    run = get_object_or_404(PayrollRun, pk=pk)

    # ✅ Allow delete for DRAFT, PROCESSED, and CANCELLED
    if run.status not in ['DRAFT', 'PROCESSED', 'CANCELLED']:
        messages.error(request, 'Only Draft, Processed, or Cancelled payroll runs can be deleted.')
        return redirect('payroll:run_detail', pk=run.pk)

    # ✅ If PROCESSED, warn about payslips
    if run.status == 'PROCESSED' and run.payslips.exists():
        messages.warning(request, 'This run has payslips. They will be deleted too.')

    if request.method == 'POST':
        run_number = run.run_number
        # Delete all payslips first
        run.payslips.all().delete()
        run.delete()
        messages.success(request, f'Payroll run {run_number} deleted successfully!')
        return redirect('payroll:run_list')

    context = {
        'run': run,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payroll Runs', 'url': '/payroll/', 'active': False},
            {'name': run.run_number, 'url': f'/payroll/{run.id}/', 'active': False},
            {'name': 'Delete', 'active': True},
        ],
    }
    return render(request, 'payroll/run_confirm_delete.html', context)