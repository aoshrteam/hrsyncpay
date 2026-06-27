# apps/statutory/admin.py
from django.contrib import admin
from .models import StatutorySettings, ProfessionalTaxSlab, PFChallan, ESIChallan, PTChallan


@admin.register(StatutorySettings)
class StatutorySettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'pt_state', 'updated_at']
    fieldsets = (
        ('PF Settings', {
            'fields': ('pf_applicable', 'pf_employee_rate', 'pf_employer_rate', 'pf_capping')
        }),
        ('EPS Settings', {
            'fields': ('eps_applicable', 'eps_employee_rate', 'eps_employer_rate', 'eps_limit')
        }),
        ('ESI Settings', {
            'fields': ('esi_applicable', 'esi_rule', 'esi_limit', 'esi_employee_rate', 'esi_employer_rate')
        }),
        ('TDS Settings', {
            'fields': ('tds_applicable', 'tds_type', 'tds_rate', 'tds_section')
        }),
        ('Professional Tax Settings', {
            'fields': ('pt_applicable', 'pt_state')
        }),
    )


@admin.register(ProfessionalTaxSlab)
class ProfessionalTaxSlabAdmin(admin.ModelAdmin):
    list_display = ['state', 'min_amount', 'max_amount', 'tax_amount', 'is_active']
    list_filter = ['state', 'is_active']
    search_fields = ['state', 'description']


@admin.register(PFChallan)
class PFChallanAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'total_amount', 'generated', 'generated_at']
    list_filter = ['generated', 'year']


@admin.register(ESIChallan)
class ESIChallanAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'total_amount', 'generated', 'generated_at']
    list_filter = ['generated', 'year']


@admin.register(PTChallan)
class PTChallanAdmin(admin.ModelAdmin):
    list_display = ['month', 'year', 'state', 'total_amount', 'generated', 'generated_at']
    list_filter = ['generated', 'year', 'state']


from django.contrib import admin

# Register your models here.
