# apps/leave/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.employees.models import Employee
from apps.clients.models import Client


class LeaveType(models.Model):
    """Leave Type Master"""

    CATEGORY_CHOICES = [
        ('ANNUAL', 'Annual Leave'),
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('COMPENSATORY', 'Compensatory Off'),
        ('LOP', 'Loss of Pay'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    days_per_year = models.IntegerField(default=12)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    max_consecutive_days = models.IntegerField(default=30)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class EmployeeLeave(models.Model):
    """Employee Leave Record"""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Core Fields
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    assignment = models.ForeignKey('employees.EmployeeAssignment', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)

    # Leave Details
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Half day support
    is_half_day = models.BooleanField(default=False)
    half_day_type = models.CharField(
        max_length=15,  # ✅ Changed from 10 to 15
        choices=[
            ('FIRST_HALF', 'First Half'),
            ('SECOND_HALF', 'Second Half'),
        ],
        blank=True,
        null=True
    )

    # Reason
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Approval
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    @property
    def leave_days(self):
        """Calculate total leave days"""
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            if self.is_half_day:
                return delta - 0.5
            return delta
        return 0

    def save(self, *args, **kwargs):
        # ✅ Auto-calculate total days
        if self.start_date and self.end_date:
            self.total_days = self.leave_days
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date.")

        # Check for overlapping leaves
        if self.status != 'CANCELLED':
            overlapping = EmployeeLeave.objects.filter(
                employee=self.employee,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
                status__in=['PENDING', 'APPROVED']
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError("Employee already has a leave request for this period.")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Leave'
        verbose_name_plural = 'Employee Leaves'


class LeaveBalance(models.Model):
    """Employee Leave Balance Tracker"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=20, help_text="e.g., 2024-25")

    total_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    balance_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type.name} ({self.financial_year})"

    class Meta:
        unique_together = ['employee', 'leave_type', 'financial_year']


from django.db import models

# Create your models here.
