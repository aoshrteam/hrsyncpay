# apps/statutory/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class StatutorySettings(models.Model):
    """Master settings for PF, ESI, PT, TDS"""

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

    # EPS Settings
    eps_applicable = models.BooleanField(default=True)
    eps_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    eps_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8.33)
    eps_limit = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)

    # ESI Settings
    esi_applicable = models.BooleanField(default=True)
    esi_rule = models.CharField(
        max_length=10,
        choices=[
            ('AUTO', 'Auto (If Gross < Limit)'),
            ('FORCE', 'Force (Always Deduct)'),
            ('EXEMPT', 'Exempt (Never Deduct)'),
        ],
        default='AUTO'
    )
    esi_limit = models.DecimalField(max_digits=10, decimal_places=2, default=21000.00)
    esi_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.75)
    esi_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.25)

    # TDS Settings
    tds_applicable = models.BooleanField(default=False)
    tds_type = models.CharField(
        max_length=10,
        choices=[
            ('PERCENTAGE', 'Percentage (%)'),
            ('FIXED', 'Fixed Amount (₹)'),
        ],
        default='PERCENTAGE'
    )
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    tds_section = models.CharField(max_length=20, default='194C')

    # PT Settings
    pt_applicable = models.BooleanField(default=True)
    pt_state = models.CharField(max_length=100, default='Rajasthan')

    # Audit
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Statutory Settings ({self.pt_state})"

    class Meta:
        verbose_name = 'Statutory Setting'
        verbose_name_plural = 'Statutory Settings'


class ProfessionalTaxSlab(models.Model):
    """Professional Tax Slabs - State wise"""

    state = models.CharField(max_length=100)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.max_amount:
            return f"{self.state}: ₹{self.min_amount} - ₹{self.max_amount} → ₹{self.tax_amount}"
        else:
            return f"{self.state}: Above ₹{self.min_amount} → ₹{self.tax_amount}"

    class Meta:
        ordering = ['state', 'min_amount']
        verbose_name = 'Professional Tax Slab'
        verbose_name_plural = 'Professional Tax Slabs'


class PFChallan(models.Model):
    """PF Challan Generation Record"""

    MONTHS = [
        ('JAN', 'January'), ('FEB', 'February'), ('MAR', 'March'),
        ('APR', 'April'), ('MAY', 'May'), ('JUN', 'June'),
        ('JUL', 'July'), ('AUG', 'August'), ('SEP', 'September'),
        ('OCT', 'October'), ('NOV', 'November'), ('DEC', 'December'),
    ]

    month = models.CharField(max_length=3, choices=MONTHS)
    year = models.IntegerField()

    # Summary amounts
    total_employees = models.IntegerField(default=0)
    total_pf_basic = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_employee_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_employer_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_eps_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_admin_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_edlis_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Reference to payroll
    payroll_run_id = models.IntegerField(null=True, blank=True)

    # Status
    generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)

    # Files
    pdf_file = models.FileField(upload_to='statutory/pf/', null=True, blank=True)
    excel_file = models.FileField(upload_to='statutory/pf/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PF Challan - {self.month} {self.year}"

    class Meta:
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']


# ✅ Add PFChallanDetail Model
class PFChallanDetail(models.Model):
    """PF Challan - Employee-wise Details"""

    challan = models.ForeignKey(PFChallan, on_delete=models.CASCADE, related_name='details')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, null=True, blank=True)

    employee_name = models.CharField(max_length=100)
    employee_code = models.CharField(max_length=20)
    assignment_code = models.CharField(max_length=50, blank=True)

    pf_basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employee_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employer_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    eps_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.employee_name} - {self.challan.month} {self.challan.year}"

    class Meta:
        unique_together = ['challan', 'employee']


class ESIChallan(models.Model):
    """ESI Challan Generation Record"""

    MONTHS = [
        ('JAN', 'January'), ('FEB', 'February'), ('MAR', 'March'),
        ('APR', 'April'), ('MAY', 'May'), ('JUN', 'June'),
        ('JUL', 'July'), ('AUG', 'August'), ('SEP', 'September'),
        ('OCT', 'October'), ('NOV', 'November'), ('DEC', 'December'),
    ]

    month = models.CharField(max_length=3, choices=MONTHS)
    year = models.IntegerField()

    # Summary amounts
    total_employee_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_employer_share = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Reference to payroll
    payroll_run_id = models.IntegerField(null=True, blank=True)

    # Status
    generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)

    # Files
    pdf_file = models.FileField(upload_to='statutory/esi/', null=True, blank=True)
    excel_file = models.FileField(upload_to='statutory/esi/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ESI Challan - {self.month} {self.year}"

    class Meta:
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']


class PTChallan(models.Model):
    """Professional Tax Challan Generation Record"""

    MONTHS = [
        ('JAN', 'January'), ('FEB', 'February'), ('MAR', 'March'),
        ('APR', 'April'), ('MAY', 'May'), ('JUN', 'June'),
        ('JUL', 'July'), ('AUG', 'August'), ('SEP', 'September'),
        ('OCT', 'October'), ('NOV', 'November'), ('DEC', 'December'),
    ]

    month = models.CharField(max_length=3, choices=MONTHS)
    year = models.IntegerField()
    state = models.CharField(max_length=100, default='Rajasthan')

    # Summary amounts
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Reference to payroll
    payroll_run_id = models.IntegerField(null=True, blank=True)

    # Status
    generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)

    # Files
    pdf_file = models.FileField(upload_to='statutory/pt/', null=True, blank=True)
    excel_file = models.FileField(upload_to='statutory/pt/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PT Challan - {self.month} {self.year}"

    class Meta:
        unique_together = ['month', 'year', 'state']
        ordering = ['-year', '-month']