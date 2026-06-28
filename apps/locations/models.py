# apps/locations/models.py
from django.db import models
from django.core.exceptions import ValidationError
from apps.clients.models import Client


class Location(models.Model):
    """Client Location/Branch Model"""

    LOCATION_TYPE_CHOICES = [
        ('HEAD_OFFICE', 'Head Office'),
        ('BRANCH', 'Branch'),
        ('WAREHOUSE', 'Warehouse'),
        ('FACTORY', 'Factory'),
        ('SITE', 'Site'),
        ('OUTLET', 'Outlet'),
        ('OTHER', 'Other'),
    ]

    # ============================================
    # BASIC DETAILS
    # ============================================
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='client_locations'
    )
    location_code = models.CharField(max_length=20, unique=True)
    location_name = models.CharField(max_length=100)
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='BRANCH'
    )
    is_head_office = models.BooleanField(default=False)

    # ============================================
    # ADDRESS DETAILS
    # ============================================
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Google Maps Latitude"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Google Maps Longitude"
    )

    # ============================================
    # GST DETAILS (Location-wise)
    # ============================================
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="GST Number for this location (if different from client)"
    )
    gst_state = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="GST State for this location"
    )
    gst_applicable = models.BooleanField(default=True)

    # ============================================
    # CONTACT DETAILS (Location-wise)
    # ============================================
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    contact_mobile = models.CharField(max_length=15, blank=True, null=True)

    # ============================================
    # BILLING SETTINGS (Location-wise)
    # ============================================
    auto_billing_enabled = models.BooleanField(
        default=False,
        help_text="Enable auto billing for this location"
    )
    commission_type = models.CharField(
        max_length=20,
        choices=[
            ('PERCENTAGE', 'Percentage'),
            ('FIXED', 'Fixed Amount'),
            ('NONE', 'None'),
        ],
        default='NONE'
    )
    commission_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    service_charge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    payment_terms = models.IntegerField(default=30)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    # ============================================
    # STATUS
    # ============================================
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    # ============================================
    # AUDIT
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_locations'
    )

    def __str__(self):
        if self.is_head_office:
            return f"{self.client.name} - {self.location_name} (Head Office)"
        return f"{self.client.name} - {self.location_name}"

    @property
    def display_name(self):
        """Display name for dropdowns"""
        return f"{self.client.name} - {self.location_name}"

    @property
    def full_address(self):
        """Complete address as string"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.pincode:
            parts.append(self.pincode)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts)

    @property
    def effective_gst(self):
        """Get effective GST (location GST or client GST)"""
        if self.gst_number:
            return self.gst_number
        return self.client.gst_number

    @property
    def effective_gst_state(self):
        """Get effective GST state"""
        if self.gst_state:
            return self.gst_state
        return self.client.gst_state

    def clean(self):
        if self.is_head_office:
            # Only one head office per client
            if Location.objects.filter(
                    client=self.client,
                    is_head_office=True
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f"{self.client.name} already has a Head Office location."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['client', 'location_code']
        ordering = ['client__name', 'location_name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'


class LocationEmployeeMapping(models.Model):
    """Track which employees are assigned to which location"""

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='location_mappings'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='employee_mappings'
    )
    assignment = models.ForeignKey(
        'employees.EmployeeAssignment',
        on_delete=models.CASCADE,
        related_name='location_mappings',
        null=True,
        blank=True
    )

    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('TRANSFERRED', 'Transferred'),
            ('COMPLETED', 'Completed'),
        ],
        default='ACTIVE'
    )

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} @ {self.location.display_name}"

    class Meta:
        unique_together = ['employee', 'location', 'start_date']
        ordering = ['-start_date']
        verbose_name = 'Location Employee Mapping'
        verbose_name_plural = 'Location Employee Mappings'


from django.db import models

# Create your models here.
