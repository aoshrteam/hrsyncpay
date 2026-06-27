# apps/leave/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from .models import LeaveType, EmployeeLeave, LeaveBalance
from .forms import LeaveTypeForm, EmployeeLeaveForm
from apps.employees.models import Employee
from apps.core.decorators import data_entry_or_admin_required


# ============================================
# LEAVE TYPE VIEWS
# ============================================

@login_required
def leave_type_list(request):
    """Leave Type List View"""
    leave_types = LeaveType.objects.all().order_by('name')

    search = request.GET.get('search')
    if search:
        leave_types = leave_types.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(category__icontains=search)
        )

    paginator = Paginator(leave_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_types': leave_types.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Leave Types', 'active': True},
        ],
    }
    return render(request, 'leave/leave_type_list.html', context)


@login_required
@data_entry_or_admin_required
def leave_type_create(request):
    """Create Leave Type"""
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            leave_type = form.save()
            messages.success(request, f'Leave Type {leave_type.name} created successfully!')
            return redirect('leave:leave_type_list')
    else:
        form = LeaveTypeForm()

    context = {
        'form': form,
        'title': 'Create Leave Type',
        'button_text': 'Save Leave Type',
    }
    return render(request, 'leave/leave_type_form.html', context)


# ============================================
# EMPLOYEE LEAVE VIEWS
# ============================================

@login_required
def leave_list(request):
    """Employee Leave List View"""
    leaves = EmployeeLeave.objects.all().order_by('-created_at')

    # Filters
    employee_id = request.GET.get('employee')
    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)

    status = request.GET.get('status')
    if status:
        leaves = leaves.filter(status=status)

    leave_type_id = request.GET.get('leave_type')
    if leave_type_id:
        leaves = leaves.filter(leave_type_id=leave_type_id)

    search = request.GET.get('search')
    if search:
        leaves = leaves.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employee_code__icontains=search) |
            Q(leave_type__name__icontains=search)
        )

    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'employees': Employee.objects.filter(is_active=True),
        'leave_types': LeaveType.objects.filter(is_active=True),
        'status_choices': EmployeeLeave.STATUS_CHOICES,
        'search': search,
        'total_leaves': leaves.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employee Leaves', 'active': True},
        ],
    }
    return render(request, 'leave/leave_list.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def leave_create(request):
    """Create Employee Leave"""
    if request.method == 'POST':
        form = EmployeeLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.created_by = request.user
            leave.save()

            messages.success(request, f'Leave request for {leave.employee.name} created successfully!')
            return redirect('leave:leave_detail', pk=leave.pk)
    else:
        form = EmployeeLeaveForm()

    context = {
        'form': form,
        'title': 'Create Leave Request',
        'button_text': 'Save Leave',
    }
    return render(request, 'leave/leave_form.html', context)


@login_required
def leave_detail(request, pk):
    """Leave Detail View"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    context = {
        'leave': leave,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employee Leaves', 'url': '/leave/', 'active': False},
            {'name': f'{leave.employee.name} - {leave.leave_type.name}', 'active': True},
        ],
    }
    return render(request, 'leave/leave_detail.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def leave_approve(request, pk):
    """Approve Leave Request"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    if leave.status != 'PENDING':
        messages.warning(request, 'Only pending leaves can be approved.')
        return redirect('leave:leave_detail', pk=leave.pk)

    if request.method == 'POST':
        leave.status = 'APPROVED'
        leave.approved_by = request.user
        leave.approved_date = timezone.now()
        leave.save()

        # Update leave balance
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave.employee,
            leave_type=leave.leave_type,
            financial_year=timezone.now().strftime('%Y') + '-' + str(timezone.now().year + 1)[2:],
            defaults={
                'total_days': leave.leave_type.days_per_year,
                'used_days': 0,
                'balance_days': leave.leave_type.days_per_year,
            }
        )
        balance.used_days += leave.total_days
        balance.balance_days = balance.total_days - balance.used_days
        balance.save()

        messages.success(request, f'Leave request approved successfully!')
        return redirect('leave:leave_detail', pk=leave.pk)

    context = {
        'leave': leave,
    }
    return render(request, 'leave/leave_confirm_approve.html', context)


@login_required
@data_entry_or_admin_required
@transaction.atomic
def leave_reject(request, pk):
    """Reject Leave Request"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    if leave.status != 'PENDING':
        messages.warning(request, 'Only pending leaves can be rejected.')
        return redirect('leave:leave_detail', pk=leave.pk)

    if request.method == 'POST':
        leave.status = 'REJECTED'
        leave.save()
        messages.success(request, 'Leave request rejected!')
        return redirect('leave:leave_detail', pk=leave.pk)

    context = {
        'leave': leave,
    }
    return render(request, 'leave/leave_confirm_reject.html', context)


@login_required
@data_entry_or_admin_required
def leave_cancel(request, pk):
    """Cancel Leave Request"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    if leave.status == 'CANCELLED':
        messages.warning(request, 'Leave is already cancelled.')
        return redirect('leave:leave_detail', pk=leave.pk)

    if request.method == 'POST':
        leave.status = 'CANCELLED'
        leave.save()

        # If approved, update balance
        if leave.status == 'APPROVED':
            balance = LeaveBalance.objects.filter(
                employee=leave.employee,
                leave_type=leave.leave_type,
                financial_year=timezone.now().strftime('%Y') + '-' + str(timezone.now().year + 1)[2:]
            ).first()
            if balance:
                balance.used_days -= leave.total_days
                balance.balance_days = balance.total_days - balance.used_days
                balance.save()

        messages.success(request, 'Leave cancelled successfully!')
        return redirect('leave:leave_list')

    context = {
        'leave': leave,
    }
    return render(request, 'leave/leave_confirm_cancel.html', context)


# apps/leave/views.py - Add these views

@login_required
@data_entry_or_admin_required
def leave_type_edit(request, pk):
    """Edit Leave Type"""
    leave_type = get_object_or_404(LeaveType, pk=pk)

    if request.method == 'POST':
        form = LeaveTypeForm(request.POST, instance=leave_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Leave Type {leave_type.name} updated successfully!')
            return redirect('leave:leave_type_list')
    else:
        form = LeaveTypeForm(instance=leave_type)

    context = {
        'form': form,
        'leave_type': leave_type,
        'title': 'Edit Leave Type',
        'button_text': 'Update Leave Type',
    }
    return render(request, 'leave/leave_type_form.html', context)


@login_required
@data_entry_or_admin_required
def leave_type_delete(request, pk):
    """Delete Leave Type"""
    leave_type = get_object_or_404(LeaveType, pk=pk)

    if request.method == 'POST':
        name = leave_type.name
        leave_type.delete()
        messages.success(request, f'Leave Type {name} deleted successfully!')
        return redirect('leave:leave_type_list')

    context = {
        'leave_type': leave_type,
    }
    return render(request, 'leave/leave_type_confirm_delete.html', context)


@login_required
@data_entry_or_admin_required
def leave_edit(request, pk):
    """Edit Employee Leave"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    if leave.status != 'PENDING':
        messages.error(request, 'Only pending leave requests can be edited.')
        return redirect('leave:leave_detail', pk=leave.pk)

    if request.method == 'POST':
        form = EmployeeLeaveForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave request updated successfully!')
            return redirect('leave:leave_detail', pk=leave.pk)
    else:
        form = EmployeeLeaveForm(instance=leave)

    context = {
        'form': form,
        'leave': leave,
        'title': 'Edit Leave Request',
        'button_text': 'Update Leave',
    }
    return render(request, 'leave/leave_form.html', context)


@login_required
@data_entry_or_admin_required
def leave_delete(request, pk):
    """Delete Employee Leave"""
    leave = get_object_or_404(EmployeeLeave, pk=pk)

    if leave.status != 'PENDING':
        messages.error(request, 'Only pending leave requests can be deleted.')
        return redirect('leave:leave_list')

    if request.method == 'POST':
        employee_name = leave.employee.name
        leave.delete()
        messages.success(request, f'Leave request for {employee_name} deleted successfully!')
        return redirect('leave:leave_list')

    context = {
        'leave': leave,
    }
    return render(request, 'leave/leave_confirm_delete.html', context)


@login_required
def leave_balance(request, employee_id):
    """View Leave Balance for Employee"""
    employee = get_object_or_404(Employee, id=employee_id)
    balances = LeaveBalance.objects.filter(employee=employee)

    context = {
        'employee': employee,
        'balances': balances,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'url': f'/employees/{employee.id}/', 'active': False},
            {'name': 'Leave Balance', 'active': True},
        ],
    }
    return render(request, 'leave/leave_balance.html', context)




# Create your views here.
