# apps/payheads/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import PayheadCategory, PayheadTemplate, AssignmentPayheadOverride
from apps.clients.models import Client


class PayheadCategoryForm(forms.ModelForm):
    """Form for creating/editing payhead categories"""

    class Meta:
        model = PayheadCategory
        fields = ['client', 'name', 'category_type', 'description', 'is_active', 'sort_order']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'category_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['category_type'].initial = 'EARNING'


class PayheadTemplateForm(forms.ModelForm):
    """Form for creating/editing payhead templates"""

    class Meta:
        model = PayheadTemplate
        fields = [
            'client', 'category', 'name', 'type', 'code', 'description',
            'calculation_type', 'default_value', 'min_value', 'max_value', 'formula',
            'is_statutory', 'is_taxable', 'is_mandatory', 'requires_approval',
            'display_order', 'is_active'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter payhead name'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BONUS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'calculation_type': forms.Select(attrs={'class': 'form-control'}),
            'default_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'formula': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                             'placeholder': 'e.g., basic_pay * 0.1 + attendance_days * 100'}),
            'is_statutory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_taxable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

        # Filter categories to only those for the selected client
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['category'].queryset = PayheadCategory.objects.filter(client_id=client_id, is_active=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.client:
            self.fields['category'].queryset = PayheadCategory.objects.filter(client=self.instance.client,
                                                                              is_active=True)
        else:
            self.fields['category'].queryset = PayheadCategory.objects.none()

        # Set default values
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['is_taxable'].initial = True
            self.fields['type'].initial = 'EARNING'
            self.fields['calculation_type'].initial = 'FIXED'
            self.fields['default_value'].initial = 0.00

    def clean(self):
        cleaned_data = super().clean()

        # Validate formula if calculation type is FORMULA
        calculation_type = cleaned_data.get('calculation_type')
        formula = cleaned_data.get('formula')

        if calculation_type == 'FORMULA' and not formula:
            self.add_error('formula', 'Formula is required for formula-based calculation.')

        # Validate min/max values
        min_value = cleaned_data.get('min_value')
        max_value = cleaned_data.get('max_value')
        default_value = cleaned_data.get('default_value')

        if min_value is not None and max_value is not None and min_value > max_value:
            self.add_error('min_value', 'Minimum value cannot be greater than maximum value.')

        if default_value is not None:
            if min_value is not None and default_value < min_value:
                self.add_error('default_value', f'Default value must be at least {min_value}.')
            if max_value is not None and default_value > max_value:
                self.add_error('default_value', f'Default value cannot exceed {max_value}.')

        return cleaned_data


class AssignmentPayheadOverrideForm(forms.ModelForm):
    """Form for overriding payhead values at assignment level"""

    class Meta:
        model = AssignmentPayheadOverride
        fields = ['payhead_template', 'overridden_value', 'reason', 'is_active']
        widgets = {
            'payhead_template': forms.Select(attrs={'class': 'form-control'}),
            'overridden_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for override'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_overridden_value(self):
        value = self.cleaned_data.get('overridden_value')
        if value is not None and value < 0:
            raise forms.ValidationError('Override value cannot be negative.')
        return value