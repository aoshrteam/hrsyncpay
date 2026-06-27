# apps/loans/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
from apps.employees.models import Employee  # ✅ Add this import
from apps.clients.models import Client  # ✅ Add this import
from .models import LoanType, EmployeeLoan, LoanDeduction
from .forms import LoanTypeForm, EmployeeLoanForm, LoanRepaymentForm
from apps.core.decorators import data_entry_or_admin_required


# ============================================
# LOAN TYPE VIEWS
# ============================================

@login_required
def loan_type_list(request):
    """Loan Type List View"""
    loan_types = LoanType.objects.all().order_by('name')

    search = request.GET.get('search')
    if search:
        loan_types = loan_types.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(category__icontains=search)
        )

    paginator = Paginator(loan_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_types': loan_types.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Loan Types', 'active': True},
        ],
    }
    return render(request, 'loans/loan_type_list.html', context)


@login_required
@data_entry_or_admin_required
def loan_type_create(request):
    """Create Loan Type"""
    if request.method == 'POST':
        form = LoanTypeForm(request.POST)
        if form.is_valid():
            loan_type = form.save()
            messages.success(request, f'Loan Type {loan_type.name} created successfully!')
            return redirect('loans:loan_type_list')
    else:
        form = LoanTypeForm()

    context = {
        'form': form,
        'title': 'Create Loan Type',
        'button_text': 'Save Loan Type',
    }
    return render(request, 'loans/loan_type_form.html', context)


@login_required
@data_entry_or_admin_required
def loan_type_edit(request, pk):
    """Edit Loan Type"""
    loan_type = get_object_or_404(LoanType, pk=pk)

    if request.method == 'POST':
        form = LoanTypeForm(request.POST, instance=loan_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Loan Type {loan_type.name} updated successfully!')
            return redirect('loans:loan_type_list')
    else:
        form = LoanTypeForm(instance=loan_type)

    context = {
        'form': form,
        'loan_type': loan_type,
        'title': 'Edit Loan Type',
        'button_text': 'Update Loan Type',
    }
    return render(request, 'loans/loan_type_form.html', context)


# ============================================
# EMPLOYEE LOAN VIEWS
# ============================================

@login_required
def loan_list(request):
    """Employee Loan List View"""
    loans = EmployeeLoan.objects.all().order_by('-created_at')

    # Filters
    employee_id = request.GET.get('employee')
    if employee_id:
        loans = loans.filter(employee_id=employee_id)

    loan_type_id = request.GET.get('loan_type')
    if loan_type_id:
        loans = loans.filter(loan_type_id=loan_type_id)

    status = request.GET.get('status')
    if status:
        loans = loans.filter(status=status)

    search = request.GET.get('search')
    if search:
        loans = loans.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employee_code__icontains=search) |
            Q(loan_type__name__icontains=search)
        )

    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'employees': Employee.objects.filter(is_active=True),
        'loan_types': LoanType.objects.filter(is_active=True),
        'status_choices': EmployeeLoan.LOAN_STATUS,
        'search': search,
        'total_loans': loans.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employee Loans', 'active': True},
        ],
    }
    return render(request, 'loans/loan_list.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def loan_create(request):
    """Create Employee Loan"""
    if request.method == 'POST':
        form = EmployeeLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.created_by = request.user

            # Calculate total amount
            loan.total_amount = loan.loan_amount + loan.interest_amount
            loan.installment_amount = loan.total_amount / Decimal(str(loan.total_installments))
            loan.installment_amount = loan.installment_amount.quantize(Decimal('0.01'))
            loan.remaining_installments = loan.total_installments

            loan.save()

            messages.success(request, f'Loan created for {loan.employee.name} successfully!')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = EmployeeLoanForm()

    context = {
        'form': form,
        'title': 'Create Employee Loan',
        'button_text': 'Save Loan',
    }
    return render(request, 'loans/loan_form.html', context)


@login_required
def loan_detail(request, pk):
    """Loan Detail View"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)
    deductions = loan.deductions.all().order_by('month_year')

    context = {
        'loan': loan,
        'deductions': deductions,
        'progress': loan.progress_percentage,
        'remaining_amount': loan.remaining_amount,
        'paid_amount': loan.paid_amount,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employee Loans', 'url': '/loans/', 'active': False},
            {'name': f'{loan.employee.name} - {loan.loan_type.name}', 'active': True},
        ],
    }
    return render(request, 'loans/loan_detail.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def loan_edit(request, pk):
    """Edit Employee Loan"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    if loan.status in ['CLOSED', 'CANCELLED']:
        messages.error(request, 'Cannot edit a closed or cancelled loan!')
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = EmployeeLoanForm(request.POST, instance=loan)
        if form.is_valid():
            loan = form.save()
            messages.success(request, f'Loan updated successfully!')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = EmployeeLoanForm(instance=loan)

    context = {
        'form': form,
        'loan': loan,
        'title': 'Edit Employee Loan',
        'button_text': 'Update Loan',
    }
    return render(request, 'loans/loan_form.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def loan_delete(request, pk):
    """Delete Employee Loan"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    if loan.status in ['ACTIVE', 'CLOSED']:
        messages.error(request, 'Cannot delete an active or closed loan!')
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        employee_name = loan.employee.name
        loan.delete()
        messages.success(request, f'Loan for {employee_name} deleted successfully!')
        return redirect('loans:loan_list')

    context = {
        'loan': loan,
    }
    return render(request, 'loans/loan_confirm_delete.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def loan_make_payment(request, pk):
    """Make manual loan payment/repayment"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    if loan.status == 'CLOSED':
        messages.error(request, 'This loan is already closed!')
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = LoanRepaymentForm(request.POST, loan=loan)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            repayment_date = form.cleaned_data['repayment_date']
            notes = form.cleaned_data.get('notes', '')

            # Create deduction record
            installment_number = loan.paid_installments + 1

            # Calculate principal and interest (approx)
            principal_portion = amount * Decimal('0.8')
            interest_portion = amount * Decimal('0.2')

            deduction = LoanDeduction.objects.create(
                employee_loan=loan,
                month_year=repayment_date.replace(day=1),
                installment_number=installment_number,
                amount=amount,
                principal_amount=principal_portion,
                interest_amount=interest_portion,
                deducted=True,
                deducted_date=repayment_date
            )

            # Update loan
            loan.paid_installments = installment_number
            loan.remaining_installments = loan.total_installments - installment_number

            if loan.remaining_installments <= 0:
                loan.status = 'CLOSED'
                loan.last_deduction_date = repayment_date

            loan.save()

            messages.success(request, f'Payment of ₹{amount} made successfully!')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = LoanRepaymentForm(loan=loan)

    context = {
        'form': form,
        'loan': loan,
        'title': 'Make Loan Payment',
        'button_text': 'Make Payment',
    }
    return render(request, 'loans/loan_payment_form.html', context)


@login_required
def loan_deduction_detail(request, pk):
    """Loan Deduction Detail View"""
    deduction = get_object_or_404(LoanDeduction, pk=pk)
    loan = deduction.employee_loan

    context = {
        'deduction': deduction,
        'loan': loan,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employee Loans', 'url': '/loans/', 'active': False},
            {'name': loan.employee.name, 'url': f'/loans/{loan.id}/', 'active': False},
            {'name': f'Installment {deduction.installment_number}', 'active': True},
        ],
    }
    return render(request, 'loans/loan_deduction_detail.html', context)


@login_required
def loan_type_list(request):
    """Loan Type List View"""
    loan_types = LoanType.objects.all().order_by('name')

    search = request.GET.get('search')
    if search:
        loan_types = loan_types.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(category__icontains=search)
        )

    paginator = Paginator(loan_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_types': loan_types.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Loan Types', 'active': True},
        ],
    }
    return render(request, 'loans/loan_type_list.html', context)