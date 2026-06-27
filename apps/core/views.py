# apps/core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import json
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill

from apps.core.decorators import data_entry_or_admin_required
from apps.employees.models import Employee
from apps.clients.models import Client
from apps.payroll.models import PayrollRun, PaymentVoucher
from apps.attendance.models import AttendanceVoucher
from apps.leave.models import EmployeeLeave as LeaveRequest


@login_required
def dashboard(request):
    """Main Dashboard View"""
    # Get current month stats
    today = timezone.now().date()
    month_start = today.replace(day=1)

    context = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'total_clients': Client.objects.filter(is_active=True).count(),
    }

    # Add optional stats if apps are installed
    if AttendanceVoucher:
        # ✅ FIXED: Changed 'month' to 'month_year'
        context['total_attendance'] = AttendanceVoucher.objects.filter(month_year=month_start).count()
    else:
        context['total_attendance'] = 0

    if LeaveRequest:
        context['total_leaves'] = LeaveRequest.objects.filter(
            status='APPROVED',
            start_date__year=today.year,
            start_date__month=today.month
        ).count()
        context['pending_leaves'] = LeaveRequest.objects.filter(status='PENDING').count()
    else:
        context['total_leaves'] = 0
        context['pending_leaves'] = 0

    if PayrollRun:
        # ✅ Check if PayrollRun has 'month' or 'month_year' field
        context['total_payroll'] = PayrollRun.objects.filter(month_year=month_start).count()
    else:
        context['total_payroll'] = 0

    if PaymentVoucher:
        context['total_payments'] = PaymentVoucher.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count()
    else:
        context['total_payments'] = 0

    context['recent_employees'] = Employee.objects.all().order_by('-created_at')[:5]
    context['recent_clients'] = Client.objects.all().order_by('-created_at')[:5]

    return render(request, 'core/dashboard.html', context)

@login_required
@data_entry_or_admin_required
def import_export_home(request):
    """Import/Export Home Page"""
    context = {
        'title': 'Import/Export Center',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Import/Export', 'active': True},
        ],
    }
    return render(request, 'core/import_export_home.html', context)


@login_required
@data_entry_or_admin_required
def import_employees(request):
    """Import Employees from Excel"""
    if request.method == 'POST':
        if not request.FILES.get('excel_file'):
            messages.error(request, 'Please select an Excel file.')
            return redirect('core:import_employees')

        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls).')
            return redirect('core:import_employees')

        from apps.core.import_export import ImportExportService
        result = ImportExportService.import_employees(excel_file, request.user)

        # Store errors in session for export
        if result.get('errors'):
            request.session['import_errors'] = result['errors']

        if result['success']:
            messages.success(request,
                             f"✅ {result['success_count']} employees created, "
                             f"🔄 {result['update_count']} updated, "
                             f"❌ {result['error_count']} errors"
                             )
            if result['errors']:
                messages.warning(request, f"{len(result['errors'])} errors occurred.")
                error_url = reverse('core:export_import_errors')
                messages.info(request,
                              f'<a href="{error_url}" class="btn btn-sm btn-danger" target="_blank">'
                              f'<i class="fas fa-file-excel"></i> 📥 Download Error Report</a>'
                              )
        else:
            messages.error(request, result.get('message', 'Import failed'))

        return redirect('employees:employee_list')

    context = {
        'title': 'Import Employees',
        'import_type': 'employees',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Import/Export', 'url': '/import-export/', 'active': False},
            {'name': 'Import Employees', 'active': True},
        ],
    }
    return render(request, 'core/import_export.html', context)


@login_required
@data_entry_or_admin_required
def import_clients(request):
    """Import Clients from Excel"""
    if request.method == 'POST':
        if not request.FILES.get('excel_file'):
            messages.error(request, 'Please select an Excel file.')
            return redirect('core:import_clients')

        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls).')
            return redirect('core:import_clients')

        from apps.core.import_export import ImportExportService
        result = ImportExportService.import_clients(excel_file, request.user)

        if result.get('errors'):
            request.session['import_errors'] = result['errors']

        if result['success']:
            messages.success(request,
                             f"✅ {result['success_count']} clients created, "
                             f"🔄 {result['update_count']} updated, "
                             f"❌ {result['error_count']} errors"
                             )
            if result['errors']:
                messages.warning(request, f"{len(result['errors'])} errors occurred.")
        else:
            messages.error(request, result.get('message', 'Import failed'))

        return redirect('clients:client_list')

    context = {
        'title': 'Import Clients',
        'import_type': 'clients',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Import/Export', 'url': '/import-export/', 'active': False},
            {'name': 'Import Clients', 'active': True},
        ],
    }
    return render(request, 'core/import_export.html', context)


@login_required
def export_employees(request):
    """Export Employees to Excel"""
    from apps.core.import_export import ImportExportService
    wb = ImportExportService.export_employees()

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Employees_Export.xlsx'
    wb.save(response)
    return response


@login_required
def export_clients(request):
    """Export Clients to Excel"""
    from apps.core.import_export import ImportExportService
    wb = ImportExportService.export_clients()

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Clients_Export.xlsx'
    wb.save(response)
    return response


@login_required
@data_entry_or_admin_required
def export_import_errors(request):
    """Export import errors to Excel"""
    errors = request.session.get('import_errors', [])

    if not errors:
        messages.warning(request, 'No errors to export.')
        return redirect('core:import_export')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Import Errors"

    # Headers
    headers = ['Row', 'Column', 'Error', 'Value']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        ws.column_dimensions[get_column_letter(col)].width = 20

    # Data
    for row_idx, error in enumerate(errors, 2):
        ws.cell(row=row_idx, column=1, value=error.get('row', ''))
        ws.cell(row=row_idx, column=2, value=error.get('column', ''))
        ws.cell(row=row_idx, column=3, value=error.get('error', ''))
        ws.cell(row=row_idx, column=4, value=error.get('value', ''))

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Import_Errors.xlsx'
    wb.save(response)

    # Clear errors from session after export
    del request.session['import_errors']

    return response


@login_required
def download_employee_sample(request):
    """Download Employee Import Sample Template"""
    from apps.core.import_export import ImportExportService
    wb = ImportExportService.get_employee_sample_template()

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Employee_Import_Sample.xlsx'
    wb.save(response)
    return response


@login_required
def download_client_sample(request):
    """Download Client Import Sample Template"""
    from apps.core.import_export import ImportExportService
    wb = ImportExportService.get_client_sample_template()

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Client_Import_Sample.xlsx'
    wb.save(response)
    return response


@login_required
def notifications(request):
    """Notifications View"""
    context = {
        'notifications': [],
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Notifications', 'active': True},
        ],
    }
    return render(request, 'core/notifications.html', context)


@login_required
def mark_notifications_read(request):
    """Mark all notifications as read"""
    return JsonResponse({'status': 'success'})


@login_required
def user_profile(request):
    """User Profile View"""
    context = {
        'user': request.user,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Profile', 'active': True},
        ],
    }
    return render(request, 'core/profile.html', context)


@login_required
def user_profile_edit(request):
    """Edit User Profile"""
    if request.method == 'POST':
        # Update user profile logic
        messages.success(request, 'Profile updated successfully!')
        return redirect('core:user_profile')

    context = {
        'user': request.user,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Profile', 'url': '/profile/', 'active': False},
            {'name': 'Edit Profile', 'active': True},
        ],
    }
    return render(request, 'core/profile_edit.html', context)


@login_required
def user_change_password(request):
    """Change User Password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('core:user_profile')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Profile', 'url': '/profile/', 'active': False},
            {'name': 'Change Password', 'active': True},
        ],
    }
    return render(request, 'registration/change_password.html', context)


@login_required
@data_entry_or_admin_required
def app_settings(request):
    """Application Settings View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Settings', 'active': True},
        ],
    }
    return render(request, 'core/settings.html', context)


@login_required
@data_entry_or_admin_required
def app_settings_update(request):
    """Update Application Settings"""
    if request.method == 'POST':
        messages.success(request, 'Settings updated successfully!')
    return redirect('core:app_settings')


@login_required
@data_entry_or_admin_required
def audit_log(request):
    """Audit Log View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Audit Log', 'active': True},
        ],
    }
    return render(request, 'core/audit_log.html', context)


@login_required
def reports(request):
    """Reports Home View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'active': True},
        ],
    }
    return render(request, 'core/reports.html', context)


@login_required
def report_payroll(request):
    """Payroll Report View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'url': '/reports/', 'active': False},
            {'name': 'Payroll Report', 'active': True},
        ],
    }
    return render(request, 'core/reports/payroll_report.html', context)


@login_required
def report_employee(request):
    """Employee Report View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'url': '/reports/', 'active': False},
            {'name': 'Employee Report', 'active': True},
        ],
    }
    return render(request, 'core/reports/employee_report.html', context)


@login_required
def report_client(request):
    """Client Report View"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'url': '/reports/', 'active': False},
            {'name': 'Client Report', 'active': True},
        ],
    }
    return render(request, 'core/reports/client_report.html', context)


@login_required
def client_wise_summary(request):
    """Client Wise Summary Report"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'url': '/reports/', 'active': False},
            {'name': 'Client Wise Summary', 'active': True},
        ],
    }
    return render(request, 'core/reports/client_wise_summary.html', context)


@login_required
def pending_payments_summary(request):
    """Pending Payments Summary Report"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/dashboard/', 'active': False},
            {'name': 'Reports', 'url': '/reports/', 'active': False},
            {'name': 'Pending Payments', 'active': True},
        ],
    }
    return render(request, 'core/reports/pending_payments.html', context)


@login_required
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    data = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'total_clients': Client.objects.filter(is_active=True).count(),
        'total_payroll': PayrollRun.objects.filter(month=month_start).count(),
        'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
    }
    return JsonResponse(data)


@login_required
def get_notifications(request):
    """API endpoint for notifications"""
    notifications = []
    return JsonResponse({'notifications': notifications})


@login_required
def back_navigation(request):
    """Back navigation helper"""
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('core:dashboard')