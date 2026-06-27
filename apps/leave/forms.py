# apps/leave/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import LeaveType, EmployeeLeave, LeaveBalance
from apps.employees.models import Employee
from apps.clients.models import Client
from django.utils import timezone

class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'code', 'category', 'days_per_year', 'is_paid', 'is_active', 'max_consecutive_days',
                  'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter leave type name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter leave code'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'days_per_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_consecutive_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if LeaveType.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Leave type code already exists!')
        return code


class EmployeeLeaveForm(forms.ModelForm):
    class Meta:
        model = EmployeeLeave
        fields = ['employee', 'leave_type', 'assignment', 'client', 'start_date', 'end_date', 'is_half_day',
                  'half_day_type', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_half_day': forms.CheckboxInput(attrs={'class': 'form-check-input', 'onchange': 'toggleHalfDay()'}),
            'half_day_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter reason'}),
        }
        labels = {
            'is_half_day': 'Half Day Leave?',
            'half_day_type': 'Half Day Type',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee')
        leave_type = cleaned_data.get('leave_type')
        is_half_day = cleaned_data.get('is_half_day', False)

        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")

        # Check if employee has enough leave balance
        if employee and leave_type:
            total_days = (end_date - start_date).days + 1
            if is_half_day:
                total_days -= 0.5

            # Get leave balance
            balance = LeaveBalance.objects.filter(
                employee=employee,
                leave_type=leave_type,
                financial_year=timezone.now().strftime('%Y') + '-' + str(timezone.now().year + 1)[2:]
            ).first()

            if balance and total_days > balance.balance_days:
                raise ValidationError(f"Not enough leave balance. Available: {balance.balance_days} days")

        return cleaned_data