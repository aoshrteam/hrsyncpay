# apps/employees/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from .models import Employee, EmployeeDocument, EmployeeAssignment
from .forms import EmployeeForm, EmployeeDocumentForm, EmployeeAssignmentForm
from apps.clients.models import Client
from apps.core.decorators import data_entry_or_admin_required
from apps.core.import_export import ImportExportService
from apps.clients.models import Client

@login_required
def employee_list(request):
    """Employee List View"""
    employees = Employee.objects.all().order_by('name')

    search = request.GET.get('search')
    if search:
        employees = employees.filter(
            Q(name__icontains=search) |
            Q(employee_code__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    is_active = request.GET.get('is_active')
    if is_active:
        employees = employees.filter(is_active=is_active == '1')

    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'is_active': is_active,
        'total_employees': employees.count(),
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
@data_entry_or_admin_required
def employee_create(request):
    """Create New Employee"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee {employee.name} created successfully!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()

    context = {
        'form': form,
        'title': 'Create Employee',
        'button_text': 'Save Employee',
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
def employee_detail(request, pk):
    """Employee Detail View"""
    employee = get_object_or_404(Employee, pk=pk)
    documents = employee.documents.all()
    assignments = employee.assignments.all()

    context = {
        'employee': employee,
        'documents': documents,
        'assignments': assignments,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'active': True},
        ],
    }
    return render(request, 'employees/employee_detail.html', context)


@login_required
@data_entry_or_admin_required
def employee_edit(request, pk):
    """Edit Employee"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee {employee.name} updated successfully!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    context = {
        'form': form,
        'employee': employee,
        'title': 'Edit Employee',
        'button_text': 'Update Employee',
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
@data_entry_or_admin_required
def employee_delete(request, pk):
    """Delete Employee"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        name = employee.name
        employee.delete()
        messages.success(request, f'Employee {name} deleted successfully!')
        return redirect('employees:employee_list')

    context = {
        'employee': employee,
    }
    return render(request, 'employees/employee_confirm_delete.html', context)


@login_required
def employee_documents(request, pk):
    """Employee Documents View"""
    employee = get_object_or_404(Employee, pk=pk)
    documents = employee.documents.all()

    context = {
        'employee': employee,
        'documents': documents,
    }
    return render(request, 'employees/employee_documents.html', context)


@login_required
@data_entry_or_admin_required
def document_upload(request, pk):
    """Upload Document for Employee"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('employees:employee_documents', pk=employee.pk)
    else:
        form = EmployeeDocumentForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'employees/document_upload.html', context)


@login_required
@data_entry_or_admin_required
def document_delete(request, pk):
    """Delete Document"""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    employee_id = document.employee.id

    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('employees:employee_documents', pk=employee_id)

    return redirect('employees:employee_documents', pk=employee_id)


@login_required
def employee_assignments(request, pk):
    """Employee Assignments View"""
    employee = get_object_or_404(Employee, pk=pk)
    assignments = employee.assignments.all()

    context = {
        'employee': employee,
        'assignments': assignments,
    }
    return render(request, 'employees/employee_assignments.html', context)


# apps/employees/views.py - Update these views

@login_required
@data_entry_or_admin_required
@transaction.atomic
def assignment_create(request, pk):
    """Create Assignment for Employee"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.employee = employee
            assignment.save()

            # ✅ Debug: Print saved data
            print(f"✅ Assignment Created: {assignment}")
            print(f"✅ Salary Heads: {assignment.salary_heads}")

            messages.success(request, f'Assignment created for {employee.name}!')
            return redirect('employees:employee_detail', pk=employee.pk)
        else:
            print(f"❌ Form errors: {form.errors}")
    else:
        initial = {
            'client': request.GET.get('client'),
            'start_date': request.GET.get('start_date'),
            'is_current': True,
        }
        form = EmployeeAssignmentForm(initial=initial)
        form.fields['client'].queryset = Client.objects.filter(is_active=True)

    context = {
        'form': form,
        'employee': employee,
        'title': 'Create Assignment',
        'button_text': 'Save Assignment',
    }
    return render(request, 'employees/assignment_form.html', context)


@login_required
@data_entry_or_admin_required
def assignment_edit(request, pk):
    """Edit Assignment"""
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)
    employee = assignment.employee

    if request.method == 'POST':
        form = EmployeeAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()

            # ✅ Debug: Print saved data
            print(f"✅ Assignment Updated: {assignment}")
            print(f"✅ Salary Heads: {assignment.salary_heads}")

            messages.success(request, 'Assignment updated successfully!')
            return redirect('employees:employee_detail', pk=employee.pk)
        else:
            print(f"❌ Form errors: {form.errors}")
    else:
        form = EmployeeAssignmentForm(instance=assignment)
        form.fields['client'].queryset = Client.objects.filter(is_active=True)

    context = {
        'form': form,
        'employee': employee,
        'assignment': assignment,
        'title': 'Edit Assignment',
        'button_text': 'Update Assignment',
    }
    return render(request, 'employees/assignment_form.html', context)


@login_required
@data_entry_or_admin_required
def assignment_delete(request, pk):
    """Delete Assignment"""
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)
    employee_id = assignment.employee.id

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('employees:employee_detail', pk=employee_id)

    return redirect('employees:employee_detail', pk=employee_id)


# ============================================
# EMPLOYEE IMPORT/EXPORT VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def employee_import(request):
    """Import Employees from Excel"""
    if request.method == 'POST':
        if not request.FILES.get('excel_file'):
            messages.error(request, 'Please select an Excel file.')
            return redirect('employees:employee_import')

        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls).')
            return redirect('employees:employee_import')

        result = ImportExportService.import_employees(excel_file, request.user)

        # ✅ Store errors in session for export
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
                # ✅ Use reverse() for URL
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
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Import/Export', 'url': '/import-export/', 'active': False},
            {'name': 'Import Employees', 'active': True},
        ],
    }
    return render(request, 'core/import_export.html', context)


@login_required
def employee_import_sample(request):
    """Download Employee Import Sample Template"""
    wb = ImportExportService.get_employee_sample_template()
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Employee_Import_Sample.xlsx'
    wb.save(response)
    return response

# apps/core/views.py - import_employees function

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
                # Show error download button
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
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Import/Export', 'url': '/import-export/', 'active': False},
            {'name': 'Import Employees', 'active': True},
        ],
    }
    return render(request, 'core/import_export.html', context)


# apps/employees/views.py - Add this view

@login_required
def service_history(request, pk):
    """Employee Service History Report"""
    employee = get_object_or_404(Employee, pk=pk)
    assignments = employee.assignments.all().order_by('start_date')

    # Calculate total service
    total_days = 0
    for assignment in assignments:
        end_date = assignment.end_date or timezone.now().date()
        days = (end_date - assignment.start_date).days
        total_days += days

    years = total_days // 365
    months = (total_days % 365) // 30
    remaining_days = total_days % 30

    # Get client list
    clients = []
    for assignment in assignments:
        if assignment.client not in clients:
            clients.append(assignment.client)

    # Get salary heads summary
    salary_heads = {}
    for assignment in assignments:
        heads = {
            'basic': assignment.monthly_basic or 0,
            'allowance': assignment.special_allowance or 0,
            'conveyance': assignment.conveyance_allowance or 0,
            'other': assignment.other_allowance or 0,
        }
        salary_heads[assignment.client.name] = heads

    context = {
        'employee': employee,
        'assignments': assignments,
        'total_service': f"{years} years {months} months {remaining_days} days",
        'total_assignments': assignments.count(),
        'total_clients': len(clients),
        'current_assignment': assignments.filter(is_current=True).first(),
        'salary_heads': salary_heads,
        'clients': clients,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'url': f'/employees/{employee.id}/', 'active': False},
            {'name': 'Service History', 'active': True},
        ],
    }
    return render(request, 'employees/service_history.html', context)


# apps/employees/views.py - Update service_history

@login_required
def service_history(request, pk):
    """Employee Service History Report"""
    employee = get_object_or_404(Employee, pk=pk)
    assignments = employee.assignments.all().order_by('start_date')

    # Calculate total service
    total_days = 0
    for assignment in assignments:
        end_date = assignment.end_date or timezone.now().date()
        days = (end_date - assignment.start_date).days
        total_days += days

    years = total_days // 365
    months = (total_days % 365) // 30
    remaining_days = total_days % 30

    # ✅ Client Summary
    client_summary = []
    for client in Client.objects.filter(assignments__employee=employee).distinct():
        client_assignments = assignments.filter(client=client)
        count = client_assignments.count()
        is_current = client_assignments.filter(is_current=True).exists()
        client_summary.append({
            'client': client,
            'count': count,
            'is_current': is_current,
        })

    context = {
        'employee': employee,
        'assignments': assignments,
        'total_service': f"{years} years {months} months {remaining_days} days",
        'total_assignments': assignments.count(),
        'total_clients': len(client_summary),
        'current_assignment': assignments.filter(is_current=True).first(),
        'client_summary': client_summary,  # ✅ Add client_summary
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'url': f'/employees/{employee.id}/', 'active': False},
            {'name': 'Service History', 'active': True},
        ],
    }
    return render(request, 'employees/service_history.html', context)

@login_required
def employee_profile(request, pk):
    """Employee Profile View"""
    employee = get_object_or_404(Employee, pk=pk)
    context = {
        'employee': employee,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'url': f'/employees/{employee.id}/', 'active': False},
            {'name': 'Profile', 'active': True},
        ],
    }
    return render(request, 'employees/employee_profile.html', context)


@login_required
def document_download(request, pk):
    """Download Employee Document"""
    document = get_object_or_404(EmployeeDocument, pk=pk)

    # Check if user has permission to view this document
    # (Optional: Add permission checks here)

    response = HttpResponse(document.document_file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.document_file.name}"'
    return response


@login_required
@data_entry_or_admin_required
def document_verify(request, pk):
    """Verify/Unverify Employee Document"""
    document = get_object_or_404(EmployeeDocument, pk=pk)

    if request.method == 'POST':
        document.is_verified = not document.is_verified
        document.save()
        status = 'verified' if document.is_verified else 'unverified'
        messages.success(request, f'Document {status} successfully!')
    else:
        # Toggle verification on GET (simpler)
        document.is_verified = not document.is_verified
        document.save()
        status = 'verified' if document.is_verified else 'unverified'
        messages.success(request, f'Document {status} successfully!')

    return redirect('employees:employee_documents', pk=document.employee.id)


@login_required
def assignment_detail(request, pk):
    """View Assignment Details"""
    assignment = get_object_or_404(EmployeeAssignment, pk=pk)
    employee = assignment.employee

    context = {
        'assignment': assignment,
        'employee': employee,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': employee.name, 'url': f'/employees/{employee.id}/', 'active': False},
            {'name': 'Assignment Details', 'active': True},
        ],
    }
    return render(request, 'employees/assignment_detail.html', context)


@login_required
def employee_export(request):
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
@data_entry_or_admin_required
def employee_bulk_delete(request):
    """Bulk Delete Employees"""
    if request.method == 'POST':
        employee_ids = request.POST.getlist('employee_ids')
        if employee_ids:
            count = Employee.objects.filter(id__in=employee_ids).delete()[0]
            messages.success(request, f'{count} employees deleted successfully!')
        else:
            messages.warning(request, 'No employees selected for deletion.')
    return redirect('employees:employee_list')


@login_required
@data_entry_or_admin_required
def employee_bulk_update_status(request):
    """Bulk Update Employee Status (Active/Inactive)"""
    if request.method == 'POST':
        employee_ids = request.POST.getlist('employee_ids')
        status = request.POST.get('status')

        if employee_ids and status in ['True', 'False']:
            is_active = status == 'True'
            count = Employee.objects.filter(id__in=employee_ids).update(is_active=is_active)
            action = 'activated' if is_active else 'deactivated'
            messages.success(request, f'{count} employees {action} successfully!')
        else:
            messages.warning(request, 'No employees selected or invalid status.')
    return redirect('employees:employee_list')


@login_required
def employee_list_report(request):
    """Employee List Report View"""
    employees = Employee.objects.all().order_by('name')

    context = {
        'employees': employees,
        'total_employees': employees.count(),
        'active_employees': employees.filter(is_active=True).count(),
        'inactive_employees': employees.filter(is_active=False).count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': 'Employee Report', 'active': True},
        ],
    }
    return render(request, 'employees/employee_list_report.html', context)


@login_required
def employee_statistics(request):
    """Employee Statistics Report"""
    from django.db.models import Count, Q
    from datetime import datetime

    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = Employee.objects.filter(is_active=False).count()

    # Gender distribution
    male_count = Employee.objects.filter(gender='M').count()
    female_count = Employee.objects.filter(gender='F').count()
    other_count = Employee.objects.filter(gender='O').count()

    # Join statistics (current year)
    current_year = datetime.now().year
    joined_this_year = Employee.objects.filter(date_of_joining__year=current_year).count()
    left_this_year = Employee.objects.filter(date_of_leaving__year=current_year).count()

    # PF applicability
    pf_applicable_count = Employee.objects.filter(pf_applicable=True).count()
    esi_applicable_count = Employee.objects.filter(esi_applicable=True).count()

    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'male_count': male_count,
        'female_count': female_count,
        'other_count': other_count,
        'joined_this_year': joined_this_year,
        'left_this_year': left_this_year,
        'pf_applicable_count': pf_applicable_count,
        'esi_applicable_count': esi_applicable_count,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Employees', 'url': '/employees/', 'active': False},
            {'name': 'Statistics', 'active': True},
        ],
    }
    return render(request, 'employees/employee_statistics.html', context)


@login_required
def employee_search(request):
    """API endpoint to search employees (AJAX)"""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'results': []})

    employees = Employee.objects.filter(
        Q(name__icontains=query) |
        Q(employee_code__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query)
    )[:20]

    results = [{
        'id': emp.id,
        'name': emp.name,
        'employee_code': emp.employee_code,
        'email': emp.email,
        'phone': emp.phone,
        'is_active': emp.is_active,
    } for emp in employees]

    return JsonResponse({'results': results})

@login_required
def get_employee_details(request, pk):
    """API endpoint to get employee details (AJAX)"""
    try:
        employee = Employee.objects.get(pk=pk)
        data = {
            'id': employee.id,
            'name': employee.name,
            'employee_code': employee.employee_code,
            'email': employee.email,
            'phone': employee.phone,
            'father_name': employee.father_name,
            'mother_name': employee.mother_name,
            'date_of_birth': employee.date_of_birth.strftime('%Y-%m-%d') if employee.date_of_birth else None,
            'gender': employee.gender,
            'pan_number': employee.pan_number,
            'aadhaar_number': employee.aadhaar_number,
            'pf_number': employee.pf_number,
            'esi_number': employee.esi_number,
            'uan_number': employee.uan_number,
            'bank_name': employee.bank_name,
            'bank_account_number': employee.bank_account_number,
            'ifsc_code': employee.ifsc_code,
            'date_of_joining': employee.date_of_joining.strftime('%Y-%m-%d') if employee.date_of_joining else None,
            'is_active': employee.is_active,
            'basic_pay': float(employee.basic_pay),
            'hra': float(employee.hra),
        }
        return JsonResponse(data)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)


@login_required
def get_employee_assignments(request, pk):
    """API endpoint to get employee assignments (AJAX)"""
    try:
        employee = Employee.objects.get(pk=pk)
        assignments = employee.assignments.all().order_by('-start_date')

        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'client': assignment.client.name,
                'client_code': assignment.client.code,
                'start_date': assignment.start_date.strftime('%Y-%m-%d'),
                'end_date': assignment.end_date.strftime('%Y-%m-%d') if assignment.end_date else None,
                'is_current': assignment.is_current,
                'status': assignment.status,
                'salary_method': assignment.salary_method,
                'monthly_basic': float(assignment.monthly_basic) if assignment.monthly_basic else None,
                'salary_heads': assignment.salary_heads,
            })

        return JsonResponse({'assignments': data})
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)