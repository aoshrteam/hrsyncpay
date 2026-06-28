# apps/locations/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Location, LocationEmployeeMapping
from apps.clients.models import Client


class LocationForm(forms.ModelForm):
    """Location Create/Edit Form"""

    class Meta:
        model = Location
        fields = [
            'client', 'location_code', 'location_name', 'location_type',
            'is_head_office', 'address', 'city', 'state', 'pincode',
            'country', 'latitude', 'longitude',
            'gst_number', 'gst_state', 'gst_applicable',
            'contact_person', 'contact_email', 'contact_phone',
            'contact_mobile', 'auto_billing_enabled', 'commission_type',
            'commission_rate', 'service_charge', 'payment_terms',
            'credit_limit', 'is_active', 'notes'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'location_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ABC-AND'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Andheri Office'
            }),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'is_head_office': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001'
            }),
            'gst_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 27AAAAA0000A1Z5'
            }),
            'gst_state': forms.TextInput(attrs={'class': 'form-control'}),
            'gst_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'auto_billing_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'commission_type': forms.Select(attrs={'class': 'form-control'}),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'service_charge': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }
        labels = {
            'location_code': 'Location Code',
            'location_name': 'Location Name',
            'is_head_office': 'This is Head Office',
            'gst_applicable': 'GST Applicable?',
            'auto_billing_enabled': 'Enable Auto Billing?',
        }
        help_texts = {
            'location_code': 'Unique code for this location (e.g., ABC-AND)',
            'gst_number': 'Leave blank to use client GST',
            'gst_state': 'Leave blank to use client GST state',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

        if not self.instance.pk:
            # Auto-generate location code
            self.fields['location_code'].initial = 'LOC-001'
            self.fields['is_active'].initial = True
            self.fields['gst_applicable'].initial = True


class LocationEmployeeMappingForm(forms.ModelForm):
    """Assign Employee to Location"""

    class Meta:
        model = LocationEmployeeMapping
        fields = [
            'employee', 'location', 'assignment',
            'start_date', 'end_date', 'is_current',
            'status', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }