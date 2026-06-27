# apps/company/admin.py
from django.contrib import admin
from .models import Company, CompanyUser


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'gst_number', 'phone', 'email', 'is_active']
    search_fields = ['name', 'code', 'gst_number', 'email']
    list_filter = ['is_active', 'state', 'country']
    fieldsets = (
        ('Basic Details', {
            'fields': ('name', 'code', 'address', 'city', 'state', 'pincode', 'country')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Statutory Details', {
            'fields': ('gst_number', 'pan_number', 'cin_number')
        }),
        ('Logo & Status', {
            'fields': ('logo', 'is_active')
        }),
        ('PF Settings', {
            'fields': ('pf_applicable', 'pf_employee_rate', 'pf_employer_rate', 'pf_capping')
        }),
        ('ESI Settings', {
            'fields': ('esi_applicable', 'esi_employee_rate', 'esi_employer_rate', 'esi_limit')
        }),
        ('GST Settings', {
            'fields': ('gst_applicable', 'gst_rate', 'gst_type')
        }),
        ('TDS Settings', {
            'fields': ('tds_applicable', 'tds_rate', 'tds_section')
        }),
        ('Financial Year', {
            'fields': ('financial_year_start', 'financial_year_end')
        }),
    )


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'is_active']
    search_fields = ['user__username', 'company__name']
    list_filter = ['role', 'is_active', 'company']