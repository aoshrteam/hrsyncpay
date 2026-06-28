# apps/payroll/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PayrollRun, PaymentVoucher, PaymentVoucherDetail
from apps.clients.models import Client
from apps.employees.models import Employee


class PayrollRunForm(forms.ModelForm):
    """Form for creating/editing Payroll Run"""

    class Meta:
        model = PayrollRun
        fields = [
            'month_year', 'client', 'notes'
        ]
        widgets = {
            'month_year': forms.DateInput(attrs={
                'type': 'month',
                'class': 'form-control'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter notes (optional)'
            }),
        }
        labels = {
            'month_year': 'Month & Year',
            'client': 'Client (Optional)',
            'notes': 'Notes',
        }
        help_texts = {
            'client': 'Leave blank to process all clients',
            'month_year': 'Select the month for payroll processing',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

        # Set default month to current month
        if not self.instance.pk and not self.initial.get('month_year'):
            self.initial['month_year'] = timezone.now().date().replace(day=1)

    def clean_month_year(self):
        month_year = self.cleaned_data.get('month_year')
        if month_year:
            # Ensure it's the first day of month
            if month_year.day != 1:
                raise ValidationError('Month must be the first day of the month.')

            # Check if payroll run already exists for this month and client
            client = self.cleaned_data.get('client')
            existing = PayrollRun.objects.filter(
                month_year=month_year,
                client=client
            ).exclude(pk=self.instance.pk)

            if existing.exists():
                client_name = client.name if client else 'All Clients'
                raise ValidationError(
                    f'Payroll run already exists for {month_year.strftime("%B %Y")} for {client_name}'
                )
        return month_year


class PaymentVoucherForm(forms.ModelForm):
    """Form for creating Payment Voucher"""

    class Meta:
        model = PaymentVoucher
        fields = [
            'payment_date', 'payment_type', 'client', 'payroll_run',
            'total_amount', 'notes'
        ]
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payroll_run': forms.Select(attrs={
                'class': 'form-control'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter notes (optional)'
            }),
        }
        labels = {
            'payment_date': 'Payment Date',
            'payment_type': 'Payment Type',
            'client': 'Client',
            'payroll_run': 'Payroll Run',
            'total_amount': 'Total Amount',
            'notes': 'Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)
        self.fields['payroll_run'].queryset = PayrollRun.objects.filter(
            status__in=['PROCESSED', 'FINALIZED', 'PAID']
        ).order_by('-month_year')

        # Set default payment date to today
        if not self.instance.pk and not self.initial.get('payment_date'):
            self.initial['payment_date'] = timezone.now().date()

        # If payroll_run is provided in GET, preselect it
        if not self.instance.pk and 'payroll_run' in self.data:
            try:
                run_id = int(self.data.get('payroll_run'))
                self.fields['payroll_run'].initial = run_id
            except (ValueError, TypeError):
                pass


class PaymentVoucherDetailForm(forms.ModelForm):
    """Form for Payment Voucher Details"""

    class Meta:
        model = PaymentVoucherDetail
        fields = [
            'employee', 'amount', 'description'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter description'
            }),
        }