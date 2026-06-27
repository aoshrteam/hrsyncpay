# apps/loans/admin.py
from django.contrib import admin
from .models import LoanType, EmployeeLoan, LoanDeduction


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'interest_rate', 'max_installments', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['category', 'is_active']


@admin.register(EmployeeLoan)
class EmployeeLoanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'loan_type', 'loan_amount', 'total_amount',
                    'installment_amount', 'paid_installments', 'status']
    search_fields = ['employee__name', 'employee__employee_code']
    list_filter = ['status', 'loan_type', 'client']
    readonly_fields = ['total_amount', 'installment_amount', 'remaining_installments']


@admin.register(LoanDeduction)
class LoanDeductionAdmin(admin.ModelAdmin):
    list_display = ['employee_loan', 'installment_number', 'amount', 'month_year', 'deducted']
    list_filter = ['deducted', 'month_year']


from django.contrib import admin

# Register your models here.
