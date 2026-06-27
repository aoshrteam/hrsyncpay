# apps/clients/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            # Basic Details
            'name', 'code',
            # Location Details
            'address', 'city', 'state', 'pincode', 'country',
            # Contact Details
            'contact_person', 'contact_email', 'contact_phone', 'website',
            # GST Details
            'gst_number', 'gst_state', 'pan_number',
            # ✅ Auto Billing Settings (New)
            'auto_billing_enabled',
            # Commission & Service Charge (Only if auto_billing_enabled)
            'commission_type', 'commission_rate', 'service_charge',
            # Payment Terms
            'payment_terms', 'credit_limit',
            # Status
            'is_active', 'notes',
            # ✅ Locations (New)
            'locations',
        ]
        widgets = {
            # Basic
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client code'}),
            # Location
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'pincode': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit pincode', 'maxlength': '6'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            # Contact
            'contact_person': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter contact person name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email (optional)'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone (optional)'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
            # GST
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter GST number'}),
            'gst_state': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter GST state (e.g., Rajasthan)'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PAN number'}),
            # ✅ Auto Billing
            'auto_billing_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleBillingFields(this.checked)'
            }),
            # Commission
            'commission_type': forms.Select(attrs={'class': 'form-control'}),
            'commission_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'service_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            # Payment
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            # Status
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
            # ✅ Locations (JSON)
            'locations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '[{"name":"Branch 1","address":"123, Jaipur","city":"Jaipur","state":"Rajasthan","pincode":"302001"}]',
                'help_text': 'JSON format for multiple locations'
            }),
        }
        labels = {
            'auto_billing_enabled': 'Enable Auto Billing?',
            'commission_type': 'Commission Type',
            'commission_rate': 'Commission Rate',
            'service_charge': 'Service Charge (%)',
            'payment_terms': 'Payment Terms (Days)',
            'credit_limit': 'Credit Limit (₹)',
            'locations': 'Multiple Locations (JSON)',
            'gst_state': 'GST State (Auto determines GST Applicable)',
        }
        help_texts = {
            'pincode': 'Enter 6-digit pincode',
            'gst_state': 'If provided, GST will be automatically applicable',
            'auto_billing_enabled': 'Enable to auto-generate invoices for this client',
            'commission_rate': 'If Percentage: enter %, If Fixed: enter amount',
            'locations': 'Add multiple client locations in JSON format',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make auto_billing_enabled fields optional initially
        self.fields['commission_type'].required = False
        self.fields['commission_rate'].required = False
        self.fields['service_charge'].required = False

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            # Remove spaces
            pincode = pincode.strip()
            # Check if 6 digits
            if not pincode.isdigit() or len(pincode) != 6:
                raise ValidationError('Pincode must be 6 digits.')
        return pincode

    def clean_locations(self):
        locations = self.cleaned_data.get('locations')
        if locations:
            try:
                import json
                # Validate JSON
                data = json.loads(locations)
                if not isinstance(data, list):
                    raise ValidationError('Locations must be a JSON array.')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format. Please check the format.')
        return locations

    def clean(self):
        cleaned_data = super().clean()
        auto_billing = cleaned_data.get('auto_billing_enabled', False)

        if auto_billing:
            # Commission type is required if auto billing is enabled
            commission_type = cleaned_data.get('commission_type')
            if not commission_type or commission_type == 'NONE':
                self.add_error('commission_type', 'Commission type is required when auto billing is enabled.')

            # Commission rate validation
            commission_rate = cleaned_data.get('commission_rate', 0)
            if commission_rate <= 0:
                self.add_error('commission_rate',
                               'Commission rate must be greater than 0 when auto billing is enabled.')

        return cleaned_data

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if Client.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Client code already exists!')
        return code

    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number')
        if gst and Client.objects.filter(gst_number=gst).exclude(pk=self.instance.pk).exists():
            raise ValidationError('GST number already exists!')
        return gst