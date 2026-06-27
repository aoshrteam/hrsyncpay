# apps/attendance/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from .models import AttendanceVoucher, AttendanceDetail
from apps.employees.models import Employee
from apps.clients.models import Client


class AttendanceVoucherForm(forms.ModelForm):
    month_year_input = forms.CharField(
        label='Month & Year',
        widget=forms.TextInput(attrs={
            'type': 'month',
            'class': 'form-control',
            'id': 'id_month_year_input',  # ✅ Explicit ID
            'placeholder': 'YYYY-MM'
        }),
        help_text='Select month and year (e.g., 2026-06)'
    )

    class Meta:
        model = AttendanceVoucher
        fields = ['client']  # Remove month_year from Meta fields
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)
        # Set default value to current month
        if not self.instance.pk:
            self.fields['month_year_input'].initial = timezone.now().strftime('%Y-%m')
        elif self.instance.month_year:
            self.fields['month_year_input'].initial = self.instance.month_year.strftime('%Y-%m')

    def clean_month_year_input(self):
        month_year_str = self.cleaned_data.get('month_year_input')
        if not month_year_str:
            raise ValidationError('Please select a month and year.')

        try:
            # Parse YYYY-MM format
            month_year = datetime.strptime(month_year_str, '%Y-%m').date()
            # Set to first day of month
            month_year = month_year.replace(day=1)
            return month_year
        except ValueError:
            raise ValidationError('Please enter a valid month in YYYY-MM format (e.g., 2026-06)')

    def save(self, commit=True):
        # Set the month_year from the cleaned input
        instance = super().save(commit=False)
        instance.month_year = self.cleaned_data.get('month_year_input')
        if commit:
            instance.save()
        return instance


class AttendanceDetailForm(forms.ModelForm):
    class Meta:
        model = AttendanceDetail
        fields = ['employee', 'days_present', 'days_absent', 'days_leave', 'overtime_hours', 'production_units',
                  'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'days_present': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'days_absent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'days_leave': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'production_units': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter notes'}),
        }
        labels = {
            'days_present': 'Days Present',
            'days_absent': 'Days Absent',
            'days_leave': 'Days Leave',
            'overtime_hours': 'Overtime Hours',
            'production_units': 'Production Units',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        present = cleaned_data.get('days_present', 0)
        absent = cleaned_data.get('days_absent', 0)
        leave = cleaned_data.get('days_leave', 0)

        total = present + absent + leave
        if total > 31:
            raise ValidationError("Total days (Present + Absent + Leave) cannot exceed 31.")
        return cleaned_data


class AttendanceImportForm(forms.Form):
    """Excel Import Form"""

    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with attendance data',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise ValidationError('Please upload a valid Excel file (.xlsx or .xls)')
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 5MB')
        return file