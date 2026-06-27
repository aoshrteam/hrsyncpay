# apps/core/import_export.py
import openpyxl
import json
import random
from decimal import Decimal
from datetime import datetime
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from apps.employees.models import Employee, EmployeeAssignment
from apps.clients.models import Client
from apps.company.models import Company


class ImportExportService:
    """Centralized Import/Export Service"""

    # ============================================
    # HELPER METHODS
    # ============================================

    @staticmethod
    def _get_value_from_cell(cell):
        if cell is None:
            return None
        if hasattr(cell, 'value'):
            value = cell.value
        else:
            value = cell
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        elif isinstance(value, bool):
            return 'Yes' if value else 'No'
        elif isinstance(value, str):
            return value.strip()
        return str(value) if value else None

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _generate_master_code():
        last = Employee.objects.all().order_by('-id').first()
        if last and last.master_code:
            try:
                num = int(''.join(filter(str.isdigit, last.master_code)))
                return f"EMP{num + 1:04d}"
            except:
                pass
        return "EMP0001"

    @staticmethod
    def _generate_employee_code():
        last = Employee.objects.all().order_by('-id').first()
        if last and last.employee_code:
            try:
                num = int(''.join(filter(str.isdigit, last.employee_code)))
                return f"EMP{num + 1:04d}"
            except:
                pass
        return "EMP0001"

    @staticmethod
    def _safe_str(val):
        if val is None:
            return ''
        return str(val).strip()

    @staticmethod
    def _get_not_null_value(val):
        """For NOT NULL fields: return empty string if blank"""
        val = ImportExportService._safe_str(val)
        return val if val else ''

    @staticmethod
    def _get_nullable_value(val):
        """For NULL allowed fields: return None if blank"""
        val = ImportExportService._safe_str(val)
        return None if val == '' else val

    # ============================================
    # EMPLOYEE IMPORT
    # ============================================

    @staticmethod
    def import_employees(excel_file, user):
        try:
            try:
                wb = openpyxl.load_workbook(excel_file, data_only=True)
            except:
                wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            if ws.title != "Employee Import":
                for sheet in wb.worksheets:
                    if sheet.title == "Employee Import":
                        ws = sheet
                        break
        except Exception as e:
            return {'success': False, 'message': f'Error reading file: {str(e)}', 'errors': [str(e)]}

        errors = []
        success_count = 0
        update_count = 0
        error_count = 0
        skipped_rows = 0

        headers = []
        for cell in ws[1]:
            if cell.value:
                headers.append(str(cell.value).strip())
            else:
                headers.append('')

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            try:
                data = {}
                for idx, header in enumerate(headers):
                    if header:
                        key = header.lower().replace(' ', '_').replace('*', '').strip()
                        cell = row[idx] if idx < len(row) else None
                        data[key] = ImportExportService._get_value_from_cell(cell)

                name = data.get('name')
                email = data.get('email')
                phone = data.get('phone')

                if not name and not email and not phone:
                    skipped_rows += 1
                    continue

                if not name or not email or not phone:
                    errors.append(f"Row {row_idx}: Required fields missing - Name: {name}, Email: {email}, Phone: {phone}")
                    error_count += 1
                    continue

                employee = None
                if data.get('pan_number'):
                    employee = Employee.objects.filter(pan_number=data.get('pan_number')).first()
                if not employee and data.get('aadhaar_number'):
                    employee = Employee.objects.filter(aadhaar_number=data.get('aadhaar_number')).first()
                if not employee and data.get('email'):
                    employee = Employee.objects.filter(email=data.get('email')).first()

                if employee:
                    ImportExportService._update_employee(employee, data)
                    update_count += 1
                else:
                    ImportExportService._create_employee(data)
                    success_count += 1

            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
                error_count += 1

        if skipped_rows > 0:
            errors.append(f"ℹ️ {skipped_rows} empty rows skipped")

        return {
            'success': True,
            'total_rows': ws.max_row - 1,
            'success_count': success_count,
            'update_count': update_count,
            'error_count': error_count,
            'skipped_rows': skipped_rows,
            'errors': errors
    }

    # ============================================
    # ✅ CREATE EMPLOYEE - Smart NULL/Empty handling
    # ============================================

    @staticmethod
    def _create_employee(data):
        """Create new employee - Smart handling of NULL and empty strings"""
        master_code = ImportExportService._generate_master_code()

        employee_code = ImportExportService._safe_str(data.get('employee_code'))
        if not employee_code:
            employee_code = ImportExportService._generate_employee_code()
        elif Employee.objects.filter(employee_code=employee_code).exists():
            employee_code = ImportExportService._generate_employee_code()

        employee = Employee.objects.create(
            master_code=master_code,
            employee_code=employee_code,
            name=ImportExportService._safe_str(data.get('name')),
            father_name=ImportExportService._get_not_null_value(data.get('father_name')),
            mother_name=ImportExportService._get_not_null_value(data.get('mother_name')),
            date_of_birth=ImportExportService._parse_date(data.get('date_of_birth')),
            gender=ImportExportService._safe_str(data.get('gender', 'M')).upper(),
            email=ImportExportService._safe_str(data.get('email')),
            phone=ImportExportService._safe_str(data.get('phone')),
            alternate_phone=ImportExportService._get_not_null_value(data.get('alternate_phone')),
            current_address=ImportExportService._get_not_null_value(data.get('current_address')),
            permanent_address=ImportExportService._get_not_null_value(data.get('permanent_address')),
            pan_number=ImportExportService._get_nullable_value(data.get('pan_number')),
            aadhaar_number=ImportExportService._get_nullable_value(data.get('aadhaar_number')),
            pf_number=ImportExportService._get_nullable_value(data.get('pf_number')),
            esi_number=ImportExportService._get_nullable_value(data.get('esi_number')),
            uan_number=ImportExportService._get_nullable_value(data.get('uan_number')),
            bank_name=ImportExportService._get_not_null_value(data.get('bank_name')),
            bank_account_number=ImportExportService._get_nullable_value(data.get('bank_account_number')),
            ifsc_code=ImportExportService._get_not_null_value(data.get('ifsc_code')),
            bank_branch=ImportExportService._get_not_null_value(data.get('bank_branch')),
            date_of_joining=ImportExportService._parse_date(data.get('date_of_joining')),
            is_active=True,
        )
        return employee

    # ============================================
    # ✅ UPDATE EMPLOYEE
    # ============================================

    @staticmethod
    def _update_employee(employee, data):
        try:
            if data.get('name'):
                employee.name = ImportExportService._safe_str(data.get('name'))
            if data.get('father_name') is not None:
                employee.father_name = ImportExportService._get_not_null_value(data.get('father_name'))
            if data.get('mother_name') is not None:
                employee.mother_name = ImportExportService._get_not_null_value(data.get('mother_name'))
            if data.get('date_of_birth'):
                employee.date_of_birth = ImportExportService._parse_date(data.get('date_of_birth'))
            if data.get('email'):
                employee.email = ImportExportService._safe_str(data.get('email'))
            if data.get('phone'):
                employee.phone = ImportExportService._safe_str(data.get('phone'))
            if data.get('pan_number') is not None:
                employee.pan_number = ImportExportService._get_nullable_value(data.get('pan_number'))
            if data.get('aadhaar_number') is not None:
                employee.aadhaar_number = ImportExportService._get_nullable_value(data.get('aadhaar_number'))
            if data.get('bank_account_number') is not None:
                employee.bank_account_number = ImportExportService._get_nullable_value(data.get('bank_account_number'))
            if data.get('bank_name') is not None:
                employee.bank_name = ImportExportService._get_not_null_value(data.get('bank_name'))
            if data.get('ifsc_code') is not None:
                employee.ifsc_code = ImportExportService._get_not_null_value(data.get('ifsc_code'))
            if data.get('bank_branch') is not None:
                employee.bank_branch = ImportExportService._get_not_null_value(data.get('bank_branch'))
            if data.get('pf_number') is not None:
                employee.pf_number = ImportExportService._get_nullable_value(data.get('pf_number'))
            if data.get('esi_number') is not None:
                employee.esi_number = ImportExportService._get_nullable_value(data.get('esi_number'))
            if data.get('uan_number') is not None:
                employee.uan_number = ImportExportService._get_nullable_value(data.get('uan_number'))
            if data.get('gender'):
                employee.gender = ImportExportService._safe_str(data.get('gender')).upper()
            if data.get('address'):
                employee.current_address = ImportExportService._get_not_null_value(data.get('address'))
            if data.get('date_of_joining'):
                employee.date_of_joining = ImportExportService._parse_date(data.get('date_of_joining'))
            employee.save()
            return True
        except Exception as e:
            print(f"Error updating employee: {e}")
            raise e

    # ============================================
    # EXPORT ERRORS TO EXCEL
    # ============================================

    @staticmethod
    def export_errors(errors, filename="Import_Errors.xlsx"):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Import Errors"

        headers = ['S.No', 'Error Description']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="DC3545", end_color="DC3545", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal="center")

        for idx, error in enumerate(errors, 1):
            ws.cell(row=idx + 1, column=1, value=idx)
            ws.cell(row=idx + 1, column=2, value=error)

        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 100

        return wb

    # ============================================
    # SAMPLE FILE GENERATION
    # ============================================

    @staticmethod
    def get_employee_sample_template():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Employee Import"

        headers = [
            'Name*', 'Father Name', 'Mother Name', 'Date of Birth (YYYY-MM-DD)', 'Gender (M/F/O)',
            'Email*', 'Phone*', 'Alternate Phone', 'Current Address', 'Permanent Address',
            'PAN Number', 'Aadhaar Number', 'PF Number', 'ESI Number', 'UAN Number',
            'Bank Name', 'Bank Account Number', 'IFSC Code', 'Bank Branch',
            'Date of Joining (YYYY-MM-DD)', 'PF Applicable (Yes/No)', 'PF Employee Rate (%)',
            'PF Employer Rate (%)', 'ESI Applicable (Yes/No)', 'ESI Rule (AUTO/FORCE/EXEMPT)',
            'ESI Limit (₹)', 'ESI Employee Rate (%)', 'ESI Employer Rate (%)',
            'TDS Applicable (Yes/No)', 'TDS Type (PERCENTAGE/FIXED)', 'TDS Value',
            'Basic Pay (₹)', 'HRA (₹)', 'Special Allowance (₹)', 'Conveyance (₹)'
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal="center", wrap_text=True)

        return wb

    @staticmethod
    def get_client_sample_template():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Client Import"

        headers = [
            'Name*', 'Code*', 'Address', 'City', 'State', 'Pincode (6-digit)', 'Country',
            'Contact Person', 'Contact Email', 'Contact Phone', 'Website',
            'GST Number', 'GST State (Auto determines GST Applicable)',
            'PAN Number',
            'Auto Billing Enabled (Yes/No)*',
            'Commission Type (PERCENTAGE/FIXED/NONE)',
            'Commission Rate',
            'Service Charge (%)',
            'Payment Terms (Days)',
            'Credit Limit (₹)',
            'Locations (JSON format) - Optional'
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal="center", wrap_text=True)

        return wb

    # ============================================
    # EXPORT EMPLOYEES
    # ============================================

    @staticmethod
    def export_employees():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Employees"

        headers = [
            'Master Code', 'Employee Code', 'Name', 'Father Name', 'Mother Name', 'Date of Birth',
            'Gender', 'Email', 'Phone', 'Address',
            'PAN Number', 'Aadhaar Number', 'PF Number', 'ESI Number',
            'Bank Name', 'Bank Account Number', 'IFSC Code',
            'Date of Joining', 'Status'
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")

        employees = Employee.objects.all()
        for row_num, emp in enumerate(employees, 2):
            ws.cell(row=row_num, column=1, value=emp.master_code)
            ws.cell(row=row_num, column=2, value=emp.employee_code)
            ws.cell(row=row_num, column=3, value=emp.name)
            ws.cell(row=row_num, column=4, value=emp.father_name)
            ws.cell(row=row_num, column=5, value=emp.mother_name)
            ws.cell(row=row_num, column=6, value=emp.date_of_birth.strftime('%Y-%m-%d') if emp.date_of_birth else '')
            ws.cell(row=row_num, column=7, value=emp.gender)
            ws.cell(row=row_num, column=8, value=emp.email)
            ws.cell(row=row_num, column=9, value=emp.phone)
            ws.cell(row=row_num, column=10, value=emp.current_address)
            ws.cell(row=row_num, column=11, value=emp.pan_number)
            ws.cell(row=row_num, column=12, value=emp.aadhaar_number)
            ws.cell(row=row_num, column=13, value=emp.pf_number)
            ws.cell(row=row_num, column=14, value=emp.esi_number)
            ws.cell(row=row_num, column=15, value=emp.bank_name)
            ws.cell(row=row_num, column=16, value=emp.bank_account_number)
            ws.cell(row=row_num, column=17, value=emp.ifsc_code)
            ws.cell(row=row_num, column=18,
                    value=emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else '')
            ws.cell(row=row_num, column=19, value='Active' if emp.is_active else 'Inactive')

        return wb

    # ============================================
    # EXPORT CLIENTS
    # ============================================

    @staticmethod
    def export_clients():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Clients"

        headers = [
            'Name', 'Code', 'Address', 'City', 'State', 'Pincode', 'Country',
            'Contact Person', 'Contact Email', 'Contact Phone',
            'GST Number', 'GST State', 'GST Applicable',
            'Auto Billing Enabled', 'Commission Type', 'Commission Rate',
            'Service Charge', 'Payment Terms', 'Credit Limit',
            'Locations'
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")

        clients = Client.objects.all()
        for row_num, client in enumerate(clients, 2):
            ws.cell(row=row_num, column=1, value=client.name)
            ws.cell(row=row_num, column=2, value=client.code)
            ws.cell(row=row_num, column=3, value=client.address)
            ws.cell(row=row_num, column=4, value=client.city)
            ws.cell(row=row_num, column=5, value=client.state)
            ws.cell(row=row_num, column=6, value=client.pincode)
            ws.cell(row=row_num, column=7, value=client.country)
            ws.cell(row=row_num, column=8, value=client.contact_person)
            ws.cell(row=row_num, column=9, value=client.contact_email)
            ws.cell(row=row_num, column=10, value=client.contact_phone)
            ws.cell(row=row_num, column=11, value=client.gst_number)
            ws.cell(row=row_num, column=12, value=client.gst_state)
            ws.cell(row=row_num, column=13, value='Yes' if client.gst_applicable else 'No')
            ws.cell(row=row_num, column=14, value='Yes' if client.auto_billing_enabled else 'No')
            ws.cell(row=row_num, column=15, value=client.get_commission_type_display())
            ws.cell(row=row_num, column=16, value=float(client.commission_rate))
            ws.cell(row=row_num, column=17, value=float(client.service_charge))
            ws.cell(row=row_num, column=18, value=client.payment_terms)
            ws.cell(row=row_num, column=19, value=float(client.credit_limit))
            ws.cell(row=row_num, column=20, value=json.dumps(client.locations) if client.locations else '')

        return wb