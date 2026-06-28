# apps/locations/admin.py
from django.contrib import admin
from .models import Location, LocationEmployeeMapping


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        'location_code', 'location_name', 'client', 'location_type',
        'is_head_office', 'is_active', 'created_at'
    ]
    list_filter = ['client', 'location_type', 'is_head_office', 'is_active']
    search_fields = [
        'location_code', 'location_name', 'client__name',
        'gst_number', 'city', 'state'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Details', {
            'fields': ('client', 'location_code', 'location_name',
                       'location_type', 'is_head_office')
        }),
        ('Address Details', {
            'fields': ('address', 'city', 'state', 'pincode', 'country',
                       'latitude', 'longitude')
        }),
        ('GST Details', {
            'fields': ('gst_number', 'gst_state', 'gst_applicable')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'contact_email',
                       'contact_phone', 'contact_mobile')
        }),
        ('Billing Settings', {
            'fields': ('auto_billing_enabled', 'commission_type',
                       'commission_rate', 'service_charge',
                       'payment_terms', 'credit_limit')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LocationEmployeeMapping)
class LocationEmployeeMappingAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'location', 'start_date', 'end_date',
        'is_current', 'status'
    ]
    list_filter = ['location', 'status', 'is_current']
    search_fields = ['employee__name', 'location__location_name']
    readonly_fields = ['created_at', 'updated_at']


from django.contrib import admin

# Register your models here.
