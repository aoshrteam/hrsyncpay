# apps/employees/models.py
from django.db import models
from django.core.exceptions import ValidationError
from apps.clients.models import Client


class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    # ============================================
    # MASTER CODE (Permanent, Never Changes)
    # ============================================
    master_code = models.CharField(max_length=20, unique=True, blank=True, null=True)  # ✅ This field

    # ============================================
    # PERSONAL DETAILS
    # ============================================
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')

    # ============================================
    # CONTACT DETAILS (Optional)
    # ============================================
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    alternate_phone = models.CharField(max_length=15, blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)

    # ============================================
    # STATUTORY IDs
    # ============================================
    pan_number = models.CharField(max_length=10, unique=True, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, unique=True, blank=True, null=True)
    pf_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    esi_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    uan_number = models.CharField(max_length=12, blank=True, null=True)

    # ============================================
    # BANK DETAILS
    # ============================================
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)

    # ============================================
    # EMPLOYMENT DETAILS
    # ============================================
    employee_code = models.CharField(max_length=20, unique=True)
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_leaving = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # ============================================
    # PHOTO
    # ============================================
    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)

    # ============================================
    # PF SETTINGS (Employee Level Override)
    # ============================================
    pf_applicable = models.BooleanField(default=True, help_text="Is PF applicable for this employee?")
    pf_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00,
                                           help_text="PF Employee Rate (%)")
    pf_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=13.00,
                                           help_text="PF Employer Rate (%)")
    pf_capping = models.CharField(
        max_length=20,
        choices=[
            ('CAPPED_15000', 'Capped at ₹15,000'),
            ('CAPPED_18000', 'Capped at ₹18,000'),
            ('FULL', 'Full Basic'),
            ('NOT_APPLICABLE', 'Not Applicable'),
        ],
        default='CAPPED_15000',
        help_text="PF Capping Rule"
    )

    # ============================================
    # EPS SETTINGS (Employee Level Override)
    # ============================================
    eps_applicable = models.BooleanField(default=True, help_text="Is EPS (Pension) applicable for this employee?")
    eps_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                            help_text="EPS Employee Rate (%)")
    eps_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8.33,
                                            help_text="EPS Employer Rate (%)")
    eps_limit = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00, help_text="EPS Wage Limit (₹)")

    # ============================================
    # ESI SETTINGS (Employee Level Override)
    # ============================================
    esi_applicable = models.BooleanField(default=True, help_text="Is ESI applicable for this employee?")
    esi_rule = models.CharField(
        max_length=10,
        choices=[
            ('AUTO', 'Auto (If Gross < ₹21,000)'),
            ('FORCE', 'Force (Always Deduct)'),
            ('EXEMPT', 'Exempt (Never Deduct)'),
        ],
        default='AUTO',
        help_text="ESI Rule"
    )
    esi_limit = models.DecimalField(max_digits=10, decimal_places=2, default=21000.00, help_text="ESI Wage Limit (₹)")
    esi_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.75,
                                            help_text="ESI Employee Rate (%)")
    esi_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.25,
                                            help_text="ESI Employer Rate (%)")

    # ============================================
    # TDS SETTINGS (Employee Level Override)
    # ============================================
    tds_applicable = models.BooleanField(default=False, help_text="Is TDS applicable for this employee?")
    tds_type = models.CharField(
        max_length=10,
        choices=[
            ('PERCENTAGE', 'Percentage (%)'),
            ('FIXED', 'Fixed Amount (₹)'),
        ],
        default='PERCENTAGE',
        help_text="TDS Type"
    )
    tds_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="TDS Rate (%) or Fixed Amount (₹)"
    )

    # ============================================
    # FIXED SALARY HEADS (Only Basic Pay & HRA)
    # ============================================
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Basic Pay (Fixed)")
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="House Rent Allowance (Fixed)")

    # ============================================
    # DYNAMIC SALARY HEADS (JSON Field)
    # ============================================
    dynamic_salary_heads = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dynamic salary heads (e.g., {'Bonus': 5000, 'Incentive': 2000, 'Special Allowance': 3000})"
    )

    # ============================================
    # FIXED DEDUCTIONS (Only TDS, Advance, Loan)
    # ============================================
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                         help_text="Loan Deduction (Fixed)")
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                            help_text="Advance Deduction (Fixed)")

    # ============================================
    # DYNAMIC DEDUCTIONS (JSON Field)
    # ============================================
    dynamic_deductions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dynamic deductions (e.g., {'Insurance': 1000, 'Professional Tax': 200, 'Union Fee': 100})"
    )

    # ============================================
    # PROFESSIONAL TAX (Fixed - PT)
    # ============================================
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Professional Tax")

    # ============================================
    # AUDIT
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.employee_code})"

    class Meta:
        ordering = ['name']

    # ============================================
    # HELPER METHODS
    # ============================================

    def get_all_salary_heads(self):
        """Get all salary heads (Fixed + Dynamic)"""
        all_heads = {}

        # Fixed heads
        if self.basic_pay and self.basic_pay > 0:
            all_heads['Basic Pay'] = float(self.basic_pay)
        if self.hra and self.hra > 0:
            all_heads['HRA'] = float(self.hra)

        # Dynamic heads
        if self.dynamic_salary_heads:
            for key, value in self.dynamic_salary_heads.items():
                if value and float(value) > 0:
                    all_heads[key] = float(value)

        return all_heads

    def get_all_deductions(self):
        """Get all deductions (Fixed + Dynamic)"""
        all_deductions = {}

        # Fixed deductions
        if self.loan_deduction and self.loan_deduction > 0:
            all_deductions['Loan'] = float(self.loan_deduction)
        if self.advance_deduction and self.advance_deduction > 0:
            all_deductions['Advance'] = float(self.advance_deduction)
        if self.professional_tax and self.professional_tax > 0:
            all_deductions['Professional Tax'] = float(self.professional_tax)

        # Dynamic deductions
        if self.dynamic_deductions:
            for key, value in self.dynamic_deductions.items():
                if value and float(value) > 0:
                    all_deductions[key] = float(value)

        return all_deductions

    def get_total_earnings(self):
        """Calculate total earnings (Fixed + Dynamic)"""
        total = float(self.basic_pay or 0) + float(self.hra or 0)

        if self.dynamic_salary_heads:
            for value in self.dynamic_salary_heads.values():
                total += float(value or 0)

        return total

    def get_total_deductions(self):
        """Calculate total deductions (Fixed + Dynamic + PT)"""
        total = float(self.loan_deduction or 0) + float(self.advance_deduction or 0) + float(self.professional_tax or 0)

        if self.dynamic_deductions:
            for value in self.dynamic_deductions.values():
                total += float(value or 0)

        return total

    def get_net_payable(self):
        """Calculate net payable (Total Earnings - Total Deductions)"""
        return self.get_total_earnings() - self.get_total_deductions()

    def add_salary_head(self, head_name, amount):
        """Add or update a dynamic salary head"""
        if not self.dynamic_salary_heads:
            self.dynamic_salary_heads = {}
        self.dynamic_salary_heads[head_name] = float(amount)
        self.save()

    def remove_salary_head(self, head_name):
        """Remove a dynamic salary head"""
        if self.dynamic_salary_heads and head_name in self.dynamic_salary_heads:
            del self.dynamic_salary_heads[head_name]
            self.save()

    def add_deduction(self, deduction_name, amount):
        """Add or update a dynamic deduction"""
        if not self.dynamic_deductions:
            self.dynamic_deductions = {}
        self.dynamic_deductions[deduction_name] = float(amount)
        self.save()

    def remove_deduction(self, deduction_name):
        """Remove a dynamic deduction"""
        if self.dynamic_deductions and deduction_name in self.dynamic_deductions:
            del self.dynamic_deductions[deduction_name]
            self.save()


class EmployeeDocument(models.Model):
    """Employee Documents - Multiple Files Upload"""

    DOCUMENT_TYPES = [
        ('AADHAR', 'Aadhar Card'),
        ('PAN', 'PAN Card'),
        ('EDUCATION_10TH', '10th Certificate'),
        ('EDUCATION_12TH', '12th Certificate'),
        ('EDUCATION_GRADUATION', 'Graduation Certificate'),
        ('EDUCATION_POST_GRADUATION', 'Post Graduation Certificate'),
        ('PREVIOUS_EMPLOYMENT', 'Previous Employment Letter'),
        ('EXPERIENCE_LETTER', 'Experience Letter'),
        ('SALARY_SLIP', 'Previous Salary Slip'),
        ('APPOINTMENT_LETTER', 'Appointment Letter'),
        ('PHOTO', 'Passport Size Photo'),
        ('SIGNATURE', 'Signature'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('PF_CARD', 'PF Card'),
        ('ESI_CARD', 'ESI Card'),
        ('MEDICAL', 'Medical Certificate'),
        ('POLICE_VERIFICATION', 'Police Verification'),
        ('OTHER', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='employee_documents/')
    document_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee} - {self.get_document_type_display()}"

    class Meta:
        ordering = ['-upload_date']


# apps/employees/models.py - Updated EmployeeAssignment

class EmployeeAssignment(models.Model):
    SALARY_METHOD_CHOICES = [
        ('CALENDAR_MONTH', 'Calendar Month'),
        ('26_DAYS_MONTH', '26-Days Month'),
        ('PER_DAY', 'Per Day'),
        ('PRODUCTION', 'Production'),
    ]

    PF_CAP_CHOICES = [
        ('CAPPED_15000', 'Capped at ₹15,000'),
        ('CAPPED_18000', 'Capped at ₹18,000'),
        ('FULL', 'Full Basic'),
        ('NOT_APPLICABLE', 'Not Applicable'),
    ]

    ESI_RULE_CHOICES = [
        ('AUTO', 'Auto (If Gross < ₹21,000)'),
        ('FORCE', 'Force (Always Deduct)'),
        ('EXEMPT', 'Exempt (Never Deduct)'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
        ('TRANSFERRED', 'Transferred'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='assignments')

    # Period
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    effective_date = models.DateField(null=True, blank=True)

    # Salary Configuration
    salary_method = models.CharField(max_length=20, choices=SALARY_METHOD_CHOICES, default='CALENDAR_MONTH')
    monthly_basic = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_day_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # ❌ REMOVED: special_allowance, conveyance_allowance, other_allowance (Now Dynamic)

    # Statutory Rules
    pf_cap = models.CharField(max_length=20, choices=PF_CAP_CHOICES, default='CAPPED_15000')
    esi_rule = models.CharField(max_length=10, choices=ESI_RULE_CHOICES, default='AUTO')

    # EPS Rule
    eps_applicable = models.BooleanField(default=True)
    eps_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8.33)
    eps_limit = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)

    # Other
    professional_tax_exempt = models.BooleanField(default=False)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Static deduction

    # ✅ Dynamic Payheads (JSON Field)
    salary_heads = models.JSONField(default=dict, blank=True, help_text="Dynamic salary heads")
    # Format: {"earnings": {"Basic": 25000, "HRA": 10000, "DA": 5000}, "deductions": {"Insurance": 500, "Advance": 1000}}

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.client} ({self.start_date})"

    @property
    def total_earnings(self):
        """Calculate total earnings from dynamic heads + basic"""
        total = self.monthly_basic or 0
        earnings = self.salary_heads.get('earnings', {})
        for amount in earnings.values():
            total += amount
        return total

    @property
    def total_deductions(self):
        """Calculate total deductions from dynamic heads + other_deductions"""
        total = self.other_deductions or 0
        deductions = self.salary_heads.get('deductions', {})
        for amount in deductions.values():
            total += amount
        return total

    def save(self, *args, **kwargs):
        if not self.effective_date:
            self.effective_date = self.start_date
        from django.utils import timezone
        today = timezone.now().date()
        if self.start_date <= today and (not self.end_date or self.end_date >= today):
            self.is_current = True
        else:
            self.is_current = False
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-start_date']