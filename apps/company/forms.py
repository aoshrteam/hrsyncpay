# apps/company/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Company, CompanyUser
from apps.accounts.models import User


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'code', 'address', 'city', 'state', 'pincode', 'country',
            'phone', 'email', 'website',
            'gst_number', 'pan_number', 'cin_number',
            'logo', 'is_active',
            # PF Settings
            'pf_applicable', 'pf_employee_rate', 'pf_employer_rate', 'pf_capping',
            # ESI Settings
            'esi_applicable', 'esi_employee_rate', 'esi_employer_rate', 'esi_limit',
            # GST Settings
            'gst_applicable', 'gst_rate', 'gst_type',
            # TDS Settings
            'tds_applicable', 'tds_rate', 'tds_section',
            # Financial Year
            'financial_year_start', 'financial_year_end'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company code'}),
            'address': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter complete address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pincode'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter GST number'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PAN number'}),
            'cin_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter CIN number'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # PF Widgets
            'pf_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pf_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_employer_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_capping': forms.Select(attrs={'class': 'form-control'}),
            # ESI Widgets
            'esi_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esi_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_employer_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # GST Widgets
            'gst_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gst_type': forms.Select(attrs={'class': 'form-control'}),
            # TDS Widgets
            'tds_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tds_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tds_section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter TDS section'}),
            # Financial Year
            'financial_year_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'financial_year_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'pf_applicable': 'PF Applicable?',
            'pf_employee_rate': 'PF Employee Rate (%)',
            'pf_employer_rate': 'PF Employer Rate (%)',
            'pf_capping': 'PF Capping Rule',
            'esi_applicable': 'ESI Applicable?',
            'esi_employee_rate': 'ESI Employee Rate (%)',
            'esi_employer_rate': 'ESI Employer Rate (%)',
            'esi_limit': 'ESI Wage Limit (₹)',
            'gst_applicable': 'GST Applicable?',
            'gst_rate': 'GST Rate (%)',
            'gst_type': 'GST Type',
            'tds_applicable': 'TDS Applicable?',
            'tds_rate': 'TDS Rate (%)',
            'tds_section': 'TDS Section',
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if Company.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Company code already exists!')
        return code

    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number')
        if gst and Company.objects.filter(gst_number=gst).exclude(pk=self.instance.pk).exists():
            raise ValidationError('GST number already exists!')
        return gst


class CompanyUserForm(forms.ModelForm):
    """Add user to company with role"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select User'
    )

    class Meta:
        model = CompanyUser
        fields = ['user', 'role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }