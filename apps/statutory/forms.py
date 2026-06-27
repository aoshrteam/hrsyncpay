# apps/statutory/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import StatutorySettings, ProfessionalTaxSlab, PFChallan, ESIChallan, PTChallan


class StatutorySettingsForm(forms.ModelForm):
    class Meta:
        model = StatutorySettings
        fields = '__all__'
        widgets = {
            # PF Widgets
            'pf_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pf_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_employer_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pf_capping': forms.Select(attrs={'class': 'form-control'}),
            # EPS Widgets
            'eps_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'eps_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'eps_employer_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'eps_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # ESI Widgets
            'esi_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esi_rule': forms.Select(attrs={'class': 'form-control'}),
            'esi_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_employee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esi_employer_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # TDS Widgets
            'tds_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tds_type': forms.Select(attrs={'class': 'form-control'}),
            'tds_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tds_section': forms.TextInput(attrs={'class': 'form-control'}),
            # PT Widgets
            'pt_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pt_state': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'pf_applicable': 'PF Applicable?',
            'pf_employee_rate': 'PF Employee Rate (%)',
            'pf_employer_rate': 'PF Employer Rate (%)',
            'pf_capping': 'PF Capping Rule',
            'eps_applicable': 'EPS Applicable?',
            'eps_employee_rate': 'EPS Employee Rate (%)',
            'eps_employer_rate': 'EPS Employer Rate (%)',
            'eps_limit': 'EPS Limit (₹)',
            'esi_applicable': 'ESI Applicable?',
            'esi_rule': 'ESI Rule',
            'esi_limit': 'ESI Limit (₹)',
            'esi_employee_rate': 'ESI Employee Rate (%)',
            'esi_employer_rate': 'ESI Employer Rate (%)',
            'tds_applicable': 'TDS Applicable?',
            'tds_type': 'TDS Type',
            'tds_rate': 'TDS Rate (%)',
            'tds_section': 'TDS Section',
            'pt_applicable': 'Professional Tax Applicable?',
            'pt_state': 'State for Professional Tax',
        }


class ProfessionalTaxSlabForm(forms.ModelForm):
    class Meta:
        model = ProfessionalTaxSlab
        fields = ['state', 'min_amount', 'max_amount', 'tax_amount', 'is_active', 'description']
        widgets = {
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount', 0)
        max_amount = cleaned_data.get('max_amount')

        if min_amount < 0:
            raise ValidationError('Minimum amount cannot be negative.')

        if max_amount and max_amount <= min_amount:
            raise ValidationError('Maximum amount must be greater than minimum amount.')

        return cleaned_data