# apps/attendance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

from .models import AttendanceVoucher, AttendanceDetail, AttendanceImportLog
from .forms import AttendanceVoucherForm, AttendanceDetailForm, AttendanceImportForm
from apps.employees.models import Employee
from apps.clients.models import Client


@login_required
def attendance_voucher_list(request):
    """Attendance Voucher List"""
    vouchers = AttendanceVoucher.objects.all().order_by('-month_year')

    # Filters
    client_id = request.GET.get('client')
    if client_id:
        vouchers = vouchers.filter(client_id=client_id)

    month = request.GET.get('month')
    if month:
        vouchers = vouchers.filter(month_year__month=month)

    year = request.GET.get('year')
    if year:
        vouchers = vouchers.filter(month_year__year=year)

    paginator = Paginator(vouchers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'clients': Client.objects.filter(is_active=True),
        'months': range(1, 13),
        'years': range(2020, timezone.now().year + 1),
    }
    return render(request, 'attendance/attendance_voucher_list.html', context)


@login_required
@transaction.atomic
def attendance_voucher_create(request):
    """Create Attendance Voucher"""
    if request.method == 'POST':
        form = AttendanceVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.created_by = request.user
            voucher.save()
            messages.success(request, f'Attendance voucher {voucher.voucher_number} created successfully!')
            return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)
    else:
        form = AttendanceVoucherForm()

    context = {
        'form': form,
        'title': 'Create Attendance Voucher',
        'button_text': 'Create Voucher',
    }
    return render(request, 'attendance/attendance_voucher_form.html', context)


@login_required
def attendance_voucher_detail(request, pk):
    """Attendance Voucher Detail"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)
    details = voucher.details.all().order_by('employee__name')

    # Summary
    total_present = sum(d.days_present for d in details)
    total_absent = sum(d.days_absent for d in details)
    total_leave = sum(d.days_leave for d in details)
    total_overtime = sum(d.overtime_hours for d in details)
    total_production = sum(d.production_units for d in details)

    context = {
        'voucher': voucher,
        'details': details,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_leave': total_leave,
        'total_overtime': total_overtime,
        'total_production': total_production,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Attendance', 'url': '/attendance/', 'active': False},
            {'name': voucher.voucher_number, 'active': True},
        ],
    }
    return render(request, 'attendance/attendance_voucher_detail.html', context)


@login_required
@transaction.atomic
def attendance_voucher_edit(request, pk):
    """Edit Attendance Voucher - Add/Edit Employee Attendance"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)

    if request.method == 'POST':
        form = AttendanceDetailForm(request.POST)
        if form.is_valid():
            detail = form.save(commit=False)
            detail.attendance_voucher = voucher
            detail.save()
            messages.success(request, f'Attendance for {detail.employee.name} added successfully!')
            return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)
    else:
        form = AttendanceDetailForm()
        # Only show employees assigned to this client
        form.fields['employee'].queryset = Employee.objects.filter(
            assignments__client=voucher.client,
            assignments__is_current=True,
            is_active=True
        ).distinct()

    # Get existing employees for this voucher
    existing_employees = voucher.details.values_list('employee_id', flat=True)

    context = {
        'voucher': voucher,
        'form': form,
        'existing_employees': existing_employees,
        'title': 'Add Attendance',
        'button_text': 'Save Attendance',
    }
    return render(request, 'attendance/attendance_voucher_edit.html', context)


@login_required
@transaction.atomic
def attendance_detail_delete(request, pk):
    """Delete Attendance Detail"""
    detail = get_object_or_404(AttendanceDetail, pk=pk)
    voucher_id = detail.attendance_voucher.id

    if request.method == 'POST':
        detail.delete()
        messages.success(request, 'Attendance record deleted successfully!')
        return redirect('attendance:attendance_voucher_detail', pk=voucher_id)

    return redirect('attendance:attendance_voucher_detail', pk=voucher_id)


@login_required
@transaction.atomic
def attendance_voucher_finalize(request, pk):
    """Finalize Attendance Voucher"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)

    if voucher.status == 'DRAFT':
        voucher.status = 'FINALIZED'
        voucher.finalized_at = timezone.now()
        voucher.save()
        messages.success(request, f'Attendance voucher {voucher.voucher_number} finalized successfully!')
    else:
        messages.warning(request, 'Voucher is already finalized.')

    return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)


@login_required
@transaction.atomic
def attendance_voucher_delete(request, pk):
    """Delete Attendance Voucher"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)

    if request.method == 'POST':
        voucher.delete()
        messages.success(request, 'Attendance voucher deleted successfully!')
        return redirect('attendance:attendance_voucher_list')

    context = {
        'voucher': voucher,
    }
    return render(request, 'attendance/attendance_voucher_confirm_delete.html', context)


# ============================================
# EXCEL IMPORT
# ============================================

# apps/attendance/views.py - Update attendance_import_excel

@login_required
@transaction.atomic
def attendance_import_excel(request, pk):
    """Import Attendance from Excel"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)

    # ✅ Debug print
    print(f"Import view called for voucher: {voucher.voucher_number}")

    if voucher.status != 'DRAFT':
        messages.error(request, 'Only draft vouchers can be imported.')
        return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)

    if request.method == 'POST':
        print("POST request received")  # ✅ Debug
        form = AttendanceImportForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")  # ✅ Debug
            excel_file = request.FILES['excel_file']
            print(f"File: {excel_file.name}")  # ✅ Debug

            try:
                # Read Excel file
                wb = openpyxl.load_workbook(excel_file, data_only=True)
                ws = wb.active

                # Get headers
                headers = []
                for cell in ws[1]:
                    if cell.value:
                        headers.append(str(cell.value).strip())
                    else:
                        headers.append('')

                print(f"Headers: {headers}")  # ✅ Debug

                imported = 0
                errors = []

                for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
                    try:
                        # Skip empty rows
                        if not row or all(cell.value is None for cell in row):
                            continue

                        # Get employee code
                        employee_code = str(row[0].value).strip() if row[0] and row[0].value else ''
                        if not employee_code:
                            errors.append(f"Row {row_idx}: Employee Code is required")
                            continue

                        # Find employee
                        employee = Employee.objects.filter(employee_code=employee_code, is_active=True).first()
                        if not employee:
                            errors.append(f"Row {row_idx}: Employee '{employee_code}' not found")
                            continue

                        # Check if employee has assignment with this client
                        if not employee.assignments.filter(client=voucher.client, is_current=True).exists():
                            errors.append(
                                f"Row {row_idx}: Employee '{employee.name}' not assigned to {voucher.client.name}")
                            continue

                        # Get attendance data
                        days_present = float(row[2].value) if len(row) > 2 and row[2] and row[2].value else 0
                        days_absent = float(row[3].value) if len(row) > 3 and row[3] and row[3].value else 0
                        days_leave = float(row[4].value) if len(row) > 4 and row[4] and row[4].value else 0
                        overtime_hours = float(row[5].value) if len(row) > 5 and row[5] and row[5].value else 0
                        production_units = int(row[6].value) if len(row) > 6 and row[6] and row[6].value else 0

                        # Create or update attendance detail
                        detail, created = AttendanceDetail.objects.get_or_create(
                            attendance_voucher=voucher,
                            employee=employee,
                            defaults={
                                'days_present': days_present,
                                'days_absent': days_absent,
                                'days_leave': days_leave,
                                'overtime_hours': overtime_hours,
                                'production_units': production_units,
                            }
                        )
                        if not created:
                            detail.days_present = days_present
                            detail.days_absent = days_absent
                            detail.days_leave = days_leave
                            detail.overtime_hours = overtime_hours
                            detail.production_units = production_units
                            detail.save()

                        imported += 1

                    except Exception as e:
                        errors.append(f"Row {row_idx}: {str(e)}")

                # Update voucher summary
                details = voucher.details.all()
                voucher.total_employees = details.count()
                voucher.total_present_days = sum(d.days_present for d in details)
                voucher.total_absent_days = sum(d.days_absent for d in details)
                voucher.total_leave_days = sum(d.days_leave for d in details)
                voucher.total_overtime_hours = sum(d.overtime_hours for d in details)
                voucher.total_production_units = sum(d.production_units for d in details)
                voucher.excel_file = excel_file
                voucher.save()

                # Log import
                AttendanceImportLog.objects.create(
                    attendance_voucher=voucher,
                    file_name=excel_file.name,
                    total_rows=ws.max_row - 1,
                    imported_rows=imported,
                    error_rows=len(errors),
                    error_details=errors
                )

                messages.success(request, f'Successfully imported {imported} attendance records!')
                if errors:
                    messages.warning(request, f'{len(errors)} errors occurred during import.')
                    for error in errors[:5]:
                        messages.warning(request, error)

                return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)

            except Exception as e:
                print(f"Error: {e}")  # ✅ Debug
                messages.error(request, f'Error reading Excel file: {str(e)}')
                return redirect('attendance:attendance_voucher_import', pk=voucher.pk)
        else:
            print(f"Form errors: {form.errors}")  # ✅ Debug
            messages.error(request, 'Invalid form data. Please check the file.')

    else:
        form = AttendanceImportForm()

    context = {
        'voucher': voucher,
        'form': form,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Attendance', 'url': '/attendance/', 'active': False},
            {'name': voucher.voucher_number, 'url': f'/attendance/{voucher.id}/', 'active': False},
            {'name': 'Import', 'active': True},
        ],
    }
    return render(request, 'attendance/attendance_voucher_import.html', context)

# ============================================
# EXCEL EXPORT
# ============================================

@login_required
def attendance_export_excel(request, pk):
    """Export Attendance to Excel"""
    voucher = get_object_or_404(AttendanceVoucher, pk=pk)
    details = voucher.details.all().order_by('employee__name')

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Headers
    headers = ['S.No', 'Employee Code', 'Employee Name', 'Days Present', 'Days Absent',
               'Days Leave', 'Overtime Hours', 'Production Units']

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border

    # Data
    for row_num, detail in enumerate(details, 2):
        ws.cell(row=row_num, column=1, value=row_num - 1)
        ws.cell(row=row_num, column=2, value=detail.employee.employee_code)
        ws.cell(row=row_num, column=3, value=detail.employee.name)
        ws.cell(row=row_num, column=4, value=float(detail.days_present))
        ws.cell(row=row_num, column=5, value=float(detail.days_absent))
        ws.cell(row=row_num, column=6, value=float(detail.days_leave))
        ws.cell(row=row_num, column=7, value=float(detail.overtime_hours))
        ws.cell(row=row_num, column=8, value=detail.production_units)

        # Apply border to all cells
        for col in range(1, 9):
            ws.cell(row=row_num, column=col).border = border

    # Auto-adjust column widths
    for col in range(1, 9):
        column_letter = get_column_letter(col)
        max_length = 0
        for row in range(1, len(details) + 2):
            cell_value = ws.cell(row=row, column=col).value
            if cell_value:
                max_length = max(max_length, len(str(cell_value)))
        ws.column_dimensions[column_letter].width = max_length + 2

    # Summary at bottom
    summary_row = len(details) + 3
    ws.cell(row=summary_row, column=1, value="SUMMARY")
    ws.cell(row=summary_row, column=1).font = Font(bold=True)

    ws.cell(row=summary_row + 1, column=1, value="Total Employees:")
    ws.cell(row=summary_row + 1, column=2, value=len(details))
    ws.cell(row=summary_row + 2, column=1, value="Total Present Days:")
    ws.cell(row=summary_row + 2, column=2, value=float(sum(d.days_present for d in details)))
    ws.cell(row=summary_row + 3, column=1, value="Total Absent Days:")
    ws.cell(row=summary_row + 3, column=2, value=float(sum(d.days_absent for d in details)))
    ws.cell(row=summary_row + 4, column=1, value="Total Leave Days:")
    ws.cell(row=summary_row + 4, column=2, value=float(sum(d.days_leave for d in details)))
    ws.cell(row=summary_row + 5, column=1, value="Total Overtime Hours:")
    ws.cell(row=summary_row + 5, column=2, value=float(sum(d.overtime_hours for d in details)))

    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Attendance_{voucher.voucher_number}.xlsx'

    wb.save(response)
    return response


@login_required
def attendance_download_template(request):
    """Download Sample Excel Template"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Template"

    # Headers
    headers = ['Employee Code', 'Employee Name', 'Days Present', 'Days Absent',
               'Days Leave', 'Overtime Hours', 'Production Units']

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Sample data
    sample_data = [
        ['EMP001', 'Rajesh Kumar', 22, 0, 2, 5, 0],
        ['EMP002', 'Priya Singh', 20, 2, 1, 3, 0],
        ['EMP003', 'Amit Patel', 23, 0, 0, 8, 10],
    ]

    for row_num, data in enumerate(sample_data, 2):
        for col_num, value in enumerate(data, 1):
            ws.cell(row=row_num, column=col_num, value=value)

    # Auto-adjust column widths
    for col in range(1, 8):
        column_letter = get_column_letter(col)
        ws.column_dimensions[column_letter].width = 20

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Attendance_Template.xlsx'

    wb.save(response)
    return response


from django.shortcuts import render

# apps/attendance/views.py - Add this helper function

from calendar import monthrange
from datetime import datetime

def get_last_day_of_month(year, month):
    """Get last day of month"""
    _, last_day = monthrange(year, month)
    return last_day

def get_attendance_date(month_year):
    """Get attendance date (last day of month)"""
    if month_year:
        year = month_year.year
        month = month_year.month
        last_day = get_last_day_of_month(year, month)
        return datetime(year, month, last_day).date()
    return timezone.now().date()


# apps/attendance/views.py - Update attendance_voucher_create

@login_required
@transaction.atomic
def attendance_voucher_create(request):
    """Create Attendance Voucher"""
    if request.method == 'POST':
        form = AttendanceVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.created_by = request.user
            voucher.save()

            # ✅ Add success message
            messages.success(request, f'Attendance voucher {voucher.voucher_number} created successfully!')

            # ✅ Redirect to detail page
            return redirect('attendance:attendance_voucher_detail', pk=voucher.pk)
        else:
            # ✅ Show form errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AttendanceVoucherForm()

    context = {
        'form': form,
        'title': 'Create Attendance Voucher',
        'button_text': 'Create Voucher',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Attendance', 'url': '/attendance/', 'active': False},
            {'name': 'Create', 'active': True},
        ],
    }
    return render(request, 'attendance/attendance_voucher_form.html', context)
# Create your views here.

