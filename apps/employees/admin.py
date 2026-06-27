# apps/employees/admin.py
from django.contrib import admin
from .models import Employee, EmployeeDocument, EmployeeAssignment


@admin.register(EmployeeAssignment)
class EmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'client', 'start_date', 'end_date', 'effective_date', 'salary_method', 'is_current',
                    'status']
    list_filter = ['client', 'salary_method', 'is_current', 'status']
    search_fields = ['employee__name', 'client__name']
    readonly_fields = ['created_at', 'updated_at']


from django.contrib import admin

# Register your models here.
