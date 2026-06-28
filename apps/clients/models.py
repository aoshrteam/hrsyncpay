# apps/clients/models.py
from django.db import models
from django.core.exceptions import ValidationError


class Client(models.Model):
    """Client Master - Manpower receiving company"""

    # ============================================
    # BASIC DETAILS
    # ============================================
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)

    # ============================================
    # LOCATION DETAILS
    # ============================================
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    country = models.CharField(max_length=100, default='India')

    # Multiple Locations (JSON field)
    locations = models.JSONField(default=list, blank=True, help_text="List of client locations")

    # ============================================
    # CONTACT DETAILS
    # ============================================
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # ============================================
    # GST DETAILS
    # ============================================
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    gst_state = models.CharField(max_length=50, blank=True, null=True, help_text="GST State for IGST/CGST calculation")

    # ✅ GST Applicable - Auto from GST State
    # If GST State provided → YES, else NO

    pan_number = models.CharField(max_length=10, blank=True, null=True)

    # ============================================
    # AUTO BILLING SETTINGS (For Future)
    # ============================================
    auto_billing_enabled = models.BooleanField(
        default=False,
        help_text="Enable auto billing for this client"
    )

    # ============================================
    # COMMISSION & SERVICE CHARGES (Only if Auto Billing = YES)
    # ============================================
    commission_type = models.CharField(
        max_length=20,
        choices=[
            ('PERCENTAGE', 'Percentage'),
            ('FIXED', 'Fixed Amount'),
            ('NONE', 'None'),
        ],
        default='NONE',
        help_text="Commission calculation type (only if auto billing enabled)"
    )
    commission_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Commission rate (in % or fixed amount)"
    )
    service_charge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Additional service charge (%)"
    )

    # ============================================
    # PAYMENT TERMS
    # ============================================
    payment_terms = models.IntegerField(default=30)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

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

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def gst_applicable(self):
        """Auto-determine GST applicability based on GST State"""
        return bool(self.gst_state)

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


# apps/clients/models.py

class ClientPayheadTemplate(models.Model):
    """Client-wise Payhead Template"""

    TEMPLATE_TYPE_CHOICES = [
        ('EARNING', 'Earning'),
        ('DEDUCTION', 'Deduction'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='client_payhead_templates'  # ✅ Changed from 'payhead_templates'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'name', 'type']
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.type})"
# apps/clients/models.py - Add these models

