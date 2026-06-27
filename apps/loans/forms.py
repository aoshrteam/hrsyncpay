# apps/loans/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import LoanType, EmployeeLoan, LoanDeduction
from apps.employees.models import Employee
from apps.clients.models import Client


class LoanTypeForm(forms.ModelForm):
    class Meta:
        model = LoanType
        fields = ['name', 'category', 'code', 'interest_rate', 'max_installments', 'is_active', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter loan type name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter loan code'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_installments': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if LoanType.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Loan code already exists!')
        return code


class EmployeeLoanForm(forms.ModelForm):
    class Meta:
        model = EmployeeLoan
        fields = [
            'employee', 'loan_type', 'client',
            'loan_amount', 'interest_amount',
            'total_installments',
            'start_date', 'end_date', 'first_deduction_date',
            'status', 'remarks'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'loan_type': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_installments': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_deduction_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter remarks'}),
        }
        labels = {
            'employee': 'Employee *',
            'loan_type': 'Loan Type *',
            'loan_amount': 'Loan Amount (₹) *',
            'interest_amount': 'Interest Amount (₹)',
            'total_installments': 'Total Installments *',
            'start_date': 'Start Date *',
            'end_date': 'End Date *',
            'first_deduction_date': 'First Deduction Date *',
        }
        help_texts = {
            'interest_amount': 'Interest amount will be added to total loan amount',
            'total_installments': 'Number of installments for repayment',
            'first_deduction_date': 'Date from which deduction will start in payroll',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)
        self.fields['loan_type'].queryset = LoanType.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        first_deduction_date = cleaned_data.get('first_deduction_date')
        loan_amount = cleaned_data.get('loan_amount', 0)
        total_installments = cleaned_data.get('total_installments', 0)

        # Validate dates
        if start_date and end_date and start_date > end_date:
            raise ValidationError('End date must be after start date!')

        if first_deduction_date and start_date and first_deduction_date < start_date:
            raise ValidationError('First deduction date must be after start date!')

        # Validate loan amount
        if loan_amount <= 0:
            raise ValidationError('Loan amount must be greater than zero!')

        # Validate installments
        if total_installments <= 0:
            raise ValidationError('Total installments must be greater than zero!')

        return cleaned_data


class LoanRepaymentForm(forms.Form):
    """Manual loan repayment form"""

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Repayment Amount (₹)'
    )
    repayment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Repayment Date'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter notes'}),
        label='Notes'
    )

    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount', 0)
        if self.loan and amount > self.loan.remaining_amount:
            raise ValidationError(f'Amount cannot exceed remaining balance: ₹{self.loan.remaining_amount}')
        if amount <= 0:
            raise ValidationError('Amount must be greater than zero!')
        return amount