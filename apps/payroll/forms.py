# apps/payroll/forms.py - Add these forms

from django import forms
from django.core.exceptions import ValidationError
from .models import PaymentVoucher, PaymentVoucherDetail, PayrollRun
from apps.clients.models import Client
from apps.employees.models import Employee


class PaymentVoucherForm(forms.ModelForm):
    class Meta:
        model = PaymentVoucher
        fields = ['payment_date', 'payment_type', 'client', 'payroll_run', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'payroll_run': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }
        labels = {
            'payment_date': 'Payment Date',
            'payment_type': 'Payment Type',
            'client': 'Client',
            'payroll_run': 'Payroll Run',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)
        self.fields['payroll_run'].queryset = PayrollRun.objects.filter(status__in=['PROCESSED', 'FINALIZED'])


class PaymentSelectionForm(forms.Form):
    """Form for selecting employees and amounts for payment"""

    def __init__(self, *args, **kwargs):
        self.payroll_run = kwargs.pop('payroll_run', None)
        super().__init__(*args, **kwargs)

        if self.payroll_run:
            payslips = self.payroll_run.payslips.filter(paid=False)
            for payslip in payslips:
                field_name = f'emp_{payslip.employee.id}'
                initial_amount = payslip.net_pay

                self.fields[field_name] = forms.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    initial=initial_amount,
                    label=f'{payslip.employee.name} (Net: ₹{initial_amount})',
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control payment-amount',
                        'step': '0.01',
                        'min': '0',
                        'max': float(initial_amount),
                        'data-employee': payslip.employee.id,
                        'data-payslip': payslip.id,
                        'data-max': float(initial_amount),
                    })
                )

                # Add checkbox for selection
                check_field_name = f'select_{payslip.employee.id}'
                self.fields[check_field_name] = forms.BooleanField(
                    initial=True,
                    required=False,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input employee-select',
                        'data-employee': payslip.employee.id,
                    })
                )

    def clean(self):
        cleaned_data = super().clean()
        total_amount = 0

        for key, value in cleaned_data.items():
            if key.startswith('emp_') and value:
                total_amount += value

        if total_amount == 0:
            raise ValidationError('Please select at least one employee with amount > 0.')

        cleaned_data['total_amount'] = total_amount
        return cleaned_data


class PaymentLedgerForm(forms.Form):
    """Form for selecting ledgers"""

    payable_ledger_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payable Ledger (Debit)'
    )
    bank_ledger_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Bank Ledger (Credit)'
    )

