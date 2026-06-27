# apps/attendance/admin.py
from django.contrib import admin
from .models import AttendanceVoucher, AttendanceDetail, AttendanceImportLog


@admin.register(AttendanceVoucher)
class AttendanceVoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_number', 'month_year', 'client', 'total_employees', 'status', 'created_at']
    list_filter = ['status', 'month_year', 'client']
    search_fields = ['voucher_number', 'client__name']
    readonly_fields = ['voucher_number', 'created_at', 'updated_at']


@admin.register(AttendanceDetail)
class AttendanceDetailAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance_voucher', 'days_present', 'days_absent', 'days_leave']
    list_filter = ['attendance_voucher__month_year', 'attendance_voucher__client']
    search_fields = ['employee__name', 'employee__employee_code']


@admin.register(AttendanceImportLog)
class AttendanceImportLogAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'attendance_voucher', 'total_rows', 'imported_rows', 'error_rows', 'import_date']
    list_filter = ['import_date']


from django.contrib import admin

# Register your models here.
