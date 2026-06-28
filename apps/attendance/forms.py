# apps/attendance/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import AttendanceVoucher, AttendanceDetail
from apps.clients.models import Client
from datetime import datetime



class AttendanceVoucherForm(forms.ModelForm):
    """Form for creating/editing attendance voucher"""

    # ✅ Separate month field for YYYY-MM input
    month = forms.CharField(
        label='Month',
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control'
        }),
        help_text='Select the month (YYYY-MM)'
    )

    class Meta:
        model = AttendanceVoucher
        fields = ['client', 'status']  # month_year removed, using month field
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'client': 'Client *',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(is_active=True)

        # If instance exists, set month value
        if self.instance and self.instance.pk and self.instance.month_year:
            self.initial['month'] = self.instance.month_year.strftime('%Y-%m')

    def clean_month(self):
        """Convert month string to date object"""
        month_value = self.cleaned_data.get('month')

        if not month_value:
            raise ValidationError('Please select a month.')

        try:
            date_obj = datetime.strptime(month_value, '%Y-%m')
            return date_obj.date()
        except ValueError:
            raise ValidationError('Please enter a valid month in YYYY-MM format.')

    def save(self, commit=True):
        """Save with month_year set from month field"""
        instance = super().save(commit=False)

        if self.cleaned_data.get('month'):
            instance.month_year = self.cleaned_data['month']
            instance.month_year = instance.month_year.replace(day=1)

        if commit:
            instance.save()

        return instance


class AttendanceDetailForm(forms.ModelForm):
    """Form for editing individual attendance detail"""

    class Meta:
        model = AttendanceDetail
        fields = ['days_present', 'days_absent', 'days_leave', 'notes']
        widgets = {
            'days_present': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'days_absent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'days_leave': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional notes'
            }),
        }
        labels = {
            'days_present': 'Days Present',
            'days_absent': 'Days Absent',
            'days_leave': 'Days Leave',
            'notes': 'Notes',
        }

    def clean(self):
        """Auto-calculate absent days"""
        cleaned_data = super().clean()
        days_present = cleaned_data.get('days_present', 0)
        days_leave = cleaned_data.get('days_leave', 0)

        if self.instance and self.instance.attendance_voucher:
            month_date = self.instance.attendance_voucher.month_year
            if month_date:
                import calendar
                total_days = calendar.monthrange(month_date.year, month_date.month)[1]

                if days_present is not None and days_leave is not None:
                    calculated_absent = total_days - days_present - days_leave
                    if calculated_absent < 0:
                        raise ValidationError('Present + Leave cannot exceed total days in month.')
                    cleaned_data['days_absent'] = max(0, calculated_absent)

        return cleaned_data


class AttendanceImportForm(forms.Form):
    """Form for importing attendance from Excel"""

    excel_file = forms.FileField(
        label='Select Excel File',
        help_text='Supported formats: .xlsx, .xls',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

    class AttendanceImportForm(forms.Form):
        """Form for importing attendance from Excel"""

        excel_file = forms.FileField(
            label='Select Excel File',
            help_text='Supported formats: .xlsx, .xls',
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls'
            })
        )


class AttendanceImportForm(forms.Form):
    """Form for importing attendance from Excel"""

    excel_file = forms.FileField(
        label='Select Excel File',
        help_text='Supported formats: .xlsx, .xls',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )