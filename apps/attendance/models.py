# apps/attendance/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.employees.models import Employee
from apps.clients.models import Client


class AttendanceVoucher(models.Model):
    """Monthly attendance voucher - No accounting link"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('FINALIZED', 'Finalized'),
        ('PROCESSED', 'Processed'),
    ]

    voucher_number = models.CharField(max_length=50, unique=True)
    month_year = models.DateField(help_text="First day of month (e.g., 2024-01-01)")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attendance_vouchers')

    # Summary
    total_employees = models.IntegerField(default=0)
    total_present_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_absent_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_leave_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_production_units = models.IntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Excel Import
    excel_file = models.FileField(upload_to='attendance_imports/', null=True, blank=True)

    # Audit
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                   related_name='attendance_vouchers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ATT-{self.month_year.strftime('%Y%m')}-{self.client.code}"

    def clean(self):
        if self.month_year:
            # Ensure month_year is first day of month
            if self.month_year.day != 1:
                raise ValidationError("Month year must be the first day of the month.")

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            month_str = self.month_year.strftime('%Y%m') if self.month_year else timezone.now().strftime('%Y%m')
            client_code = self.client.code if self.client else '000'
            self.voucher_number = f"ATT-{month_str}-{client_code}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['month_year', 'client']
        ordering = ['-month_year']
        verbose_name = 'Attendance Voucher'
        verbose_name_plural = 'Attendance Vouchers'


class AttendanceDetail(models.Model):
    """Employee-wise attendance details"""

    attendance_voucher = models.ForeignKey(AttendanceVoucher, on_delete=models.CASCADE, related_name='details')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    # Attendance
    days_present = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    days_absent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    days_leave = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Overtime & Production
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    production_units = models.IntegerField(default=0)

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.attendance_voucher.month_year.strftime('%b %Y')}"

    class Meta:
        unique_together = ['attendance_voucher', 'employee']
        ordering = ['employee__name']
        verbose_name = 'Attendance Detail'
        verbose_name_plural = 'Attendance Details'


class AttendanceImportLog(models.Model):
    """Track Excel imports"""

    attendance_voucher = models.ForeignKey(AttendanceVoucher, on_delete=models.CASCADE, related_name='import_logs')
    file_name = models.CharField(max_length=255)
    total_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    import_date = models.DateTimeField(auto_now_add=True)
    error_details = models.JSONField(default=list)

    def __str__(self):
        return f"{self.file_name} - {self.import_date}"

    class Meta:
        ordering = ['-import_date']


from django.db import models

# Create your models here.
