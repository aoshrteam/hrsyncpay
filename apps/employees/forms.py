# apps/employees/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Employee, EmployeeDocument, EmployeeAssignment
from apps.clients.models import Client
from apps.locations.models import Location
from apps.payheads.models import Payhead
import re
import os
import json


class EmployeeForm(forms.ModelForm):
    """Complete Employee Form with Dynamic Salary Heads and Deductions"""

    class Meta:
        model = Employee
        fields = [
            # Personal Details
            'name', 'father_name', 'mother_name',
            'date_of_birth', 'gender',

            # Contact Details (Optional)
            'email', 'phone', 'alternate_phone',
            'current_address', 'permanent_address',

            # Statutory IDs
            'pan_number', 'aadhaar_number', 'pf_number', 'esi_number', 'uan_number',

            # Bank Details
            'bank_name', 'bank_account_number', 'ifsc_code', 'bank_branch',

            # Employment
            'employee_code', 'date_of_joining', 'date_of_leaving',
            'is_active', 'photo',

            # PF Settings
            'pf_applicable', 'pf_employee_rate', 'pf_employer_rate', 'pf_capping',

            # EPS Settings
            'eps_applicable', 'eps_employee_rate', 'eps_employer_rate', 'eps_limit',

            # ESI Settings
            'esi_applicable', 'esi_rule', 'esi_limit', 'esi_employee_rate', 'esi_employer_rate',

            # TDS Settings
            'tds_applicable', 'tds_type', 'tds_value',

            'basic_pay', 'hra',
            'loan_deduction', 'advance_deduction',
        ]

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter employee full name', 'required': True}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter father name'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mother name'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'employee_code': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter employee code', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address (optional)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number (optional)'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternate phone'}),
            'current_address': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter current address'}),
            'permanent_address': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter permanent address'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PAN number'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Aadhaar number'}),
            'pf_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PF number'}),
            'esi_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ESI number'}),
            'uan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter UAN number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name'}),
            'bank_account_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter account number'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter IFSC code'}),
            'bank_branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank branch'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_leaving': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'pf_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pf_employee_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '12.00'}),
            'pf_employer_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '13.00'}),
            'pf_capping': forms.Select(attrs={'class': 'form-control'}),
            'eps_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'eps_employee_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'eps_employer_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '8.33'}),
            'eps_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '15000'}),
            'esi_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esi_rule': forms.Select(attrs={'class': 'form-control'}),
            'esi_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '21000'}),
            'esi_employee_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.75'}),
            'esi_employer_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '3.25'}),
            'tds_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tds_type': forms.Select(attrs={'class': 'form-control'}),
            'tds_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '10.00'}),
            'basic_pay': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter basic pay'}),
            'hra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter HRA'}),
            'loan_deduction': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter loan deduction'}),
            'advance_deduction': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter advance deduction'}),
        }

        labels = {
            'name': 'Employee Name *',
            'employee_code': 'Employee Code *',
            'father_name': 'Father Name',
            'mother_name': 'Mother Name',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'email': 'Email (Optional)',
            'phone': 'Phone (Optional)',
            'alternate_phone': 'Alternate Phone',
            'current_address': 'Current Address',
            'permanent_address': 'Permanent Address',
            'pan_number': 'PAN Number',
            'aadhaar_number': 'Aadhaar Number',
            'pf_number': 'PF Number',
            'esi_number': 'ESI Number',
            'uan_number': 'UAN Number',
            'bank_name': 'Bank Name',
            'bank_account_number': 'Bank Account Number',
            'ifsc_code': 'IFSC Code',
            'bank_branch': 'Bank Branch',
            'date_of_joining': 'Date of Joining',
            'date_of_leaving': 'Date of Leaving',
            'is_active': 'Is Active?',
            'photo': 'Photo',
            'pf_applicable': 'PF Applicable?',
            'pf_employee_rate': 'PF Employee Rate (%)',
            'pf_employer_rate': 'PF Employer Rate (%)',
            'pf_capping': 'PF Capping Rule',
            'eps_applicable': 'EPS (Pension) Applicable?',
            'eps_employee_rate': 'EPS Employee Rate (%)',
            'eps_employer_rate': 'EPS Employer Rate (%)',
            'eps_limit': 'EPS Wage Limit (₹)',
            'esi_applicable': 'ESI Applicable?',
            'esi_rule': 'ESI Rule',
            'esi_limit': 'ESI Wage Limit (₹)',
            'esi_employee_rate': 'ESI Employee Rate (%)',
            'esi_employer_rate': 'ESI Employer Rate (%)',
            'tds_applicable': 'TDS Applicable?',
            'tds_type': 'TDS Type',
            'tds_value': 'TDS Rate / Amount',
            'basic_pay': 'Basic Pay (₹)',
            'hra': 'HRA (₹)',
            'loan_deduction': 'Loan Deduction (₹)',
            'advance_deduction': 'Advance Deduction (₹)',
        }

        help_texts = {
            'pf_applicable': 'Uncheck if PF is not applicable for this employee.',
            'eps_applicable': 'Check if EPS (Pension) is applicable for this employee.',
            'eps_employer_rate': 'Usually 8.33% for EPS.',
            'eps_limit': 'Usually ₹15,000 for EPS calculation.',
            'esi_applicable': 'Uncheck if ESI is not applicable for this employee.',
            'esi_rule': 'Auto: If Gross < Limit, Force: Always deduct, Exempt: Never deduct.',
            'tds_applicable': 'Check if TDS is applicable for this employee.',
            'tds_type': 'Percentage or Fixed Amount.',
            'tds_value': 'If Percentage: enter %, If Fixed: enter amount in ₹.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['phone'].required = False

        if not self.instance.pk:
            self.fields['pf_applicable'].initial = True
            self.fields['pf_employee_rate'].initial = 12.00
            self.fields['pf_employer_rate'].initial = 13.00
            self.fields['pf_capping'].initial = 'CAPPED_15000'
            self.fields['eps_applicable'].initial = True
            self.fields['eps_employer_rate'].initial = 8.33
            self.fields['eps_limit'].initial = 15000.00
            self.fields['esi_applicable'].initial = True
            self.fields['esi_rule'].initial = 'AUTO'
            self.fields['esi_limit'].initial = 21000.00
            self.fields['esi_employee_rate'].initial = 0.75
            self.fields['esi_employer_rate'].initial = 3.25
            self.fields['tds_applicable'].initial = False
            self.fields['tds_type'].initial = 'PERCENTAGE'
            self.fields['tds_value'].initial = 0.00

    def clean_employee_code(self):
        code = self.cleaned_data.get('employee_code')
        if not code:
            raise ValidationError('Employee code is required.')
        if Employee.objects.filter(employee_code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Employee code already exists!')
        return code

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number')
        if pan:
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan.upper()):
                raise ValidationError('Invalid PAN number format. Should be like: ABCDE1234F')
            if Employee.objects.filter(pan_number=pan.upper()).exclude(pk=self.instance.pk).exists():
                raise ValidationError('PAN number already exists!')
            return pan.upper()
        return pan

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar:
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                raise ValidationError('Aadhaar number must be 12 digits.')
            if Employee.objects.filter(aadhaar_number=aadhaar).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Aadhaar number already exists!')
        return aadhaar

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if Employee.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Email already exists!')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not phone.isdigit():
                raise ValidationError('Phone number must contain only digits.')
            if len(phone) < 10 or len(phone) > 15:
                raise ValidationError('Phone number must be between 10 and 15 digits.')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        pf_applicable = cleaned_data.get('pf_applicable')
        eps_applicable = cleaned_data.get('eps_applicable')
        if eps_applicable and not pf_applicable:
            self.add_error('eps_applicable', 'EPS cannot be applicable if PF is not applicable.')
        date_of_joining = cleaned_data.get('date_of_joining')
        date_of_leaving = cleaned_data.get('date_of_leaving')
        if date_of_joining and date_of_leaving and date_of_leaving < date_of_joining:
            self.add_error('date_of_leaving', 'Date of leaving cannot be before date of joining.')
        return cleaned_data


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'document_file', 'document_name', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(
                attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
            'document_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document name'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter description'}),
        }

    def clean_document_file(self):
        file = self.cleaned_data.get('document_file')
        if file:
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be less than 5MB.')
            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            if ext not in allowed_extensions:
                raise ValidationError(f'File type not allowed. Allowed: {", ".join(allowed_extensions)}')
        return file


class EmployeeAssignmentForm(forms.ModelForm):
    """
    Employee Assignment Form with Dynamic Payheads
    """

    class Meta:
        model = EmployeeAssignment
        fields = [
            'client', 'location', 'start_date', 'end_date', 'effective_date',
            'salary_method', 'monthly_basic', 'per_day_rate', 'rate_per_unit',
            'pf_cap', 'esi_rule',
            'eps_applicable', 'eps_employer_rate', 'eps_limit',
            'professional_tax_exempt', 'other_deductions',
            'status',
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_client',
                'onchange': 'loadLocations(this.value)'
            }),
            'location': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_location'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary_method': forms.Select(attrs={'class': 'form-control'}),
            'monthly_basic': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter monthly basic'}),
            'per_day_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter per day rate'}),
            'rate_per_unit': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter rate per unit'}),
            'pf_cap': forms.Select(attrs={'class': 'form-control'}),
            'esi_rule': forms.Select(attrs={'class': 'form-control'}),
            'eps_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'eps_employer_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '8.33'}),
            'eps_limit': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '15000.00'}),
            'professional_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'other_deductions': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'client': 'Client *',
            'location': 'Location',
            'start_date': 'Start Date *',
            'end_date': 'End Date',
            'effective_date': 'Effective Date',
            'salary_method': 'Salary Calculation Method *',
            'monthly_basic': 'Monthly Basic Salary (₹)',
            'per_day_rate': 'Per Day Rate (₹)',
            'rate_per_unit': 'Rate Per Unit (₹)',
            'pf_cap': 'PF Capping Rule *',
            'esi_rule': 'ESI Rule *',
            'eps_applicable': 'EPS (Pension) Applicable?',
            'eps_employer_rate': 'EPS Employer Rate (%)',
            'eps_limit': 'EPS Wage Limit (₹)',
            'professional_tax_exempt': 'Professional Tax Exempt?',
            'other_deductions': 'Other Fixed Deduction (₹)',
            'status': 'Assignment Status',
        }

        help_texts = {
            'location': 'Select the location where employee works',
            'effective_date': 'Date from which this assignment is effective',
            'status': 'Status of this assignment',
            'eps_applicable': 'Check if EPS (Pension) is applicable',
            'other_deductions': 'Fixed deduction that applies every month',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['client'].queryset = Client.objects.filter(is_active=True)
        self.fields['location'].queryset = Location.objects.none()

        if self.instance and self.instance.pk and self.instance.client:
            self.fields['location'].queryset = Location.objects.filter(
                client=self.instance.client,
                is_active=True
            )
        elif self.initial and self.initial.get('client'):
            try:
                client_id = self.initial.get('client')
                if client_id:
                    self.fields['location'].queryset = Location.objects.filter(
                        client_id=client_id,
                        is_active=True
                    )
            except:
                pass

        # ✅ Add dynamic payhead fields
        self.payhead_fields = []
        payheads = Payhead.objects.filter(is_active=True).order_by('type', 'name')

        existing_heads = {}
        if self.instance and self.instance.pk and self.instance.salary_heads:
            existing_heads = self.instance.salary_heads

        for payhead in payheads:
            field_name = f"payhead_{payhead.id}"
            self.payhead_fields.append(field_name)

            current_value = 0
            payhead_type = payhead.type

            if payhead_type in ['EARNING', 'BONUS', 'ALLOWANCE', 'REIMBURSEMENT']:
                current_value = existing_heads.get('earnings', {}).get(payhead.name, 0)
            else:
                current_value = existing_heads.get('deductions', {}).get(payhead.name, 0)

            type_icons = {
                'EARNING': '💚', 'DEDUCTION': '❤️', 'STATUTORY_DEDUCTION': '🧡',
                'REIMBURSEMENT': '💙', 'LOAN': '💜', 'BONUS': '💛', 'ALLOWANCE': '🩵',
            }
            icon = type_icons.get(payhead_type, '⬜')

            self.fields[field_name] = forms.DecimalField(
                required=False,
                initial=current_value,
                label=f"{icon} {payhead.name}",
                help_text=payhead.description or payhead.get_type_display(),
                widget=forms.NumberInput(attrs={
                    'class': 'form-control payhead-input',
                    'step': '0.01',
                    'min': '0',
                    'data-payhead-id': payhead.id,
                    'data-payhead-type': payhead_type,
                    'data-payhead-name': payhead.name,
                    'placeholder': '0.00'
                })
            )

        if not self.instance.pk and not self.initial.get('effective_date'):
            self.initial['effective_date'] = self.initial.get('start_date')
        if not self.instance.pk and not self.initial.get('status'):
            self.initial['status'] = 'ACTIVE'
        if not self.instance.pk:
            self.initial['eps_applicable'] = True
            self.initial['eps_employer_rate'] = 8.33
            self.initial['eps_limit'] = 15000.00

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        effective_date = cleaned_data.get('effective_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError('End date must be after start date.')
        if effective_date and start_date and effective_date < start_date:
            raise ValidationError('Effective date cannot be before start date.')
        salary_method = cleaned_data.get('salary_method')
        monthly_basic = cleaned_data.get('monthly_basic')
        per_day_rate = cleaned_data.get('per_day_rate')
        rate_per_unit = cleaned_data.get('rate_per_unit')
        if salary_method == 'CALENDAR_MONTH' and not monthly_basic:
            self.add_error('monthly_basic', 'Monthly basic is required for Calendar Month method.')
        if salary_method == '26_DAYS_MONTH' and not monthly_basic:
            self.add_error('monthly_basic', 'Monthly basic is required for 26-Days Month method.')
        if salary_method == 'PER_DAY' and not per_day_rate:
            self.add_error('per_day_rate', 'Per day rate is required for Per Day method.')
        if salary_method == 'PRODUCTION' and not rate_per_unit:
            self.add_error('rate_per_unit', 'Rate per unit is required for Production method.')
        pf_cap = cleaned_data.get('pf_cap')
        eps_applicable = cleaned_data.get('eps_applicable')
        if eps_applicable and pf_cap == 'NOT_APPLICABLE':
            self.add_error('eps_applicable', 'EPS cannot be applicable if PF is not applicable.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        earnings = {}
        deductions = {}
        for field_name in self.payhead_fields:
            value = self.cleaned_data.get(field_name)
            if value and float(value) > 0:
                payhead_id = field_name.replace('payhead_', '')
                try:
                    payhead = Payhead.objects.get(id=payhead_id)
                    if payhead.type in ['EARNING', 'BONUS', 'ALLOWANCE', 'REIMBURSEMENT']:
                        earnings[payhead.name] = float(value)
                    else:
                        deductions[payhead.name] = float(value)
                except Payhead.DoesNotExist:
                    pass
        instance.salary_heads = {'earnings': earnings, 'deductions': deductions}
        if commit:
            instance.save()
        return instance


class EmployeeAssignmentFilterForm(forms.Form):
    """Form for filtering employee assignments"""
    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All')] + EmployeeAssignment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    salary_method = forms.ChoiceField(
        choices=[('', 'All')] + EmployeeAssignment.SALARY_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError('Start date must be before end date.')
        return cleaned_data