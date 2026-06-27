# apps/loans/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from apps.employees.models import Employee
from apps.clients.models import Client


class LoanType(models.Model):
    """Loan Type Master"""

    LOAN_CATEGORY = [
        ('UNIFORM', 'Uniform'),
        ('INSURANCE', 'Insurance'),
        ('MEDICAL', 'Medical'),
        ('ADVANCE', 'Advance Salary'),
        ('FESTIVAL', 'Festival Advance'),
        ('VEHICLE', 'Vehicle Loan'),
        ('HOME', 'Home Loan'),
        ('EDUCATION', 'Education Loan'),
        ('PERSONAL', 'Personal Loan'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=LOAN_CATEGORY)
    code = models.CharField(max_length=20, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_installments = models.IntegerField(default=12)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']
        verbose_name = 'Loan Type'
        verbose_name_plural = 'Loan Types'


class EmployeeLoan(models.Model):
    """Employee Loan Details"""

    LOAN_STATUS = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DEFAULTED', 'Defaulted'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Core Fields
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)

    # Loan Details
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Installments
    total_installments = models.IntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_installments = models.IntegerField(default=0)
    remaining_installments = models.IntegerField()

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    first_deduction_date = models.DateField()
    last_deduction_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='PENDING')
    remarks = models.TextField(blank=True)

    # Audit
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_loans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.loan_type.name} - ₹{self.loan_amount}"

    @property
    def remaining_amount(self):
        paid_amount = self.paid_installments * self.installment_amount
        return self.total_amount - paid_amount

    @property
    def paid_amount(self):
        return self.paid_installments * self.installment_amount

    @property
    def progress_percentage(self):
        if self.total_installments > 0:
            return (self.paid_installments / self.total_installments) * 100
        return 0

    def save(self, *args, **kwargs):
        self.total_amount = self.loan_amount + self.interest_amount
        if self.total_installments > 0:
            self.installment_amount = self.total_amount / Decimal(str(self.total_installments))
            self.installment_amount = self.installment_amount.quantize(Decimal('0.01'))
        self.remaining_installments = self.total_installments - self.paid_installments
        if self.remaining_installments <= 0 and self.status != 'CLOSED':
            self.status = 'CLOSED'
            self.last_deduction_date = timezone.now().date()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Loan'
        verbose_name_plural = 'Employee Loans'


class LoanDeduction(models.Model):
    """Track monthly loan deductions during payroll"""

    employee_loan = models.ForeignKey(EmployeeLoan, on_delete=models.CASCADE, related_name='deductions')
    month_year = models.DateField(help_text="First day of month")
    installment_number = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ Fix: Use models.ForeignKey with string reference or remove temporarily
    # Option 1: Keep as IntegerField (temporary)
    process_voucher_detail_id = models.IntegerField(null=True, blank=True,
                                                    help_text="Reference to Process Voucher Detail ID")

    # Option 2: If you want to keep ForeignKey, uncomment and use string reference
    # process_voucher_detail = models.ForeignKey('payroll.Payslip', on_delete=models.SET_NULL, null=True, blank=True)

    deducted = models.BooleanField(default=False)
    deducted_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_loan.employee.name} - Installment {self.installment_number} - ₹{self.amount}"

    class Meta:
        ordering = ['month_year', 'installment_number']
        unique_together = ['employee_loan', 'installment_number']
        verbose_name = 'Loan Deduction'
        verbose_name_plural = 'Loan Deductions'