# apps/company/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


# ✅ Django settings configure होने के बाद ही get_user_model() call करें
# User = get_user_model()  # ❌ Remove this line - causes error

class Company(models.Model):
    """Company/Organization Model"""

    # Basic Details
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')

    # Contact Details
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Statutory Details
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    cin_number = models.CharField(max_length=21, blank=True, null=True)

    # Logo
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)

    # Settings
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ Use settings.AUTH_USER_MODEL instead of get_user_model()
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_companies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # PF Settings
    pf_applicable = models.BooleanField(default=True)
    pf_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    pf_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=13.00)
    pf_capping = models.CharField(
        max_length=20,
        choices=[
            ('CAPPED_15000', 'Capped at ₹15,000'),
            ('CAPPED_18000', 'Capped at ₹18,000'),
            ('FULL', 'Full Basic'),
            ('NOT_APPLICABLE', 'Not Applicable'),
        ],
        default='CAPPED_15000'
    )

    # ESI Settings
    esi_applicable = models.BooleanField(default=True)
    esi_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.75)
    esi_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.25)
    esi_limit = models.DecimalField(max_digits=10, decimal_places=2, default=21000.00)

    # GST Settings
    gst_applicable = models.BooleanField(default=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    gst_type = models.CharField(
        max_length=10,
        choices=[
            ('CGST_SGST', 'CGST + SGST'),
            ('IGST', 'IGST'),
        ],
        default='CGST_SGST'
    )

    # TDS Settings
    tds_applicable = models.BooleanField(default=True)
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    tds_section = models.CharField(max_length=20, default='194C')

    # Financial Year
    financial_year_start = models.DateField(null=True, blank=True)
    financial_year_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'


class CompanyUser(models.Model):
    """Company wise user roles and permissions"""

    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('DATA_ENTRY', 'Data Entry'),
        ('VIEWER', 'Viewer'),
        ('ACCOUNTANT', 'Accountant'),
        ('HR', 'HR Manager'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_users')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ Use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='company_users'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    is_active = models.BooleanField(default=True)

    # Permissions
    can_create_employee = models.BooleanField(default=False)
    can_edit_employee = models.BooleanField(default=False)
    can_delete_employee = models.BooleanField(default=False)
    can_create_client = models.BooleanField(default=False)
    can_edit_client = models.BooleanField(default=False)
    can_delete_client = models.BooleanField(default=False)
    can_process_payroll = models.BooleanField(default=False)
    can_make_payment = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_manage_settings = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.role})"

    class Meta:
        unique_together = ['company', 'user']
        ordering = ['company', 'role', 'user__username']