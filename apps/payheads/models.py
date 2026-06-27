# apps/payheads/models.py
from django.db import models
from apps.clients.models import Client
from django.core.exceptions import ValidationError


class PayheadCategory(models.Model):
    """Category for grouping payheads (Earnings, Deductions, Reimbursements, etc.)"""

    CATEGORY_CHOICES = [
        ('EARNING', 'Earning'),
        ('DEDUCTION', 'Deduction'),
        ('REIMBURSEMENT', 'Reimbursement'),
        ('BONUS', 'Bonus'),
        ('ALLOWANCE', 'Allowance'),
        ('OTHER', 'Other'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payhead_categories')
    name = models.CharField(max_length=50)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='EARNING')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'name']
        ordering = ['sort_order', 'name']
        verbose_name = 'Payhead Category'
        verbose_name_plural = 'Payhead Categories'

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.get_category_type_display()})"

    def clean(self):
        if not self.name:
            raise ValidationError('Category name is required.')
        # Ensure unique name per client (case-insensitive)
        if PayheadCategory.objects.filter(
                client=self.client,
                name__iexact=self.name
        ).exclude(pk=self.pk).exists():
            raise ValidationError(f'Category "{self.name}" already exists for this client.')


class PayheadTemplate(models.Model):
    """Client-level payhead template - defines payheads that apply to all assignments"""

    PAYHEAD_TYPES = [
        ('EARNING', 'Earning'),
        ('DEDUCTION', 'Deduction'),
        ('REIMBURSEMENT', 'Reimbursement'),
        ('BONUS', 'Bonus'),
        ('ALLOWANCE', 'Allowance'),
        ('OTHER', 'Other'),
    ]

    CALCULATION_TYPES = [
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage of Basic'),
        ('PERCENTAGE_GROSS', 'Percentage of Gross'),
        ('PER_DAY', 'Per Day'),
        ('PER_UNIT', 'Per Unit'),
        ('SLAB', 'Slab Based'),
        ('FORMULA', 'Formula Based'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payhead_templates')
    category = models.ForeignKey(PayheadCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='payheads')

    # Payhead Details
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=PAYHEAD_TYPES, default='EARNING')
    code = models.CharField(max_length=20, blank=True, help_text="Short code for reporting")
    description = models.TextField(blank=True)

    # Calculation Settings
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES, default='FIXED')
    default_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    min_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    formula = models.TextField(blank=True, help_text="Python expression for formula-based calculation")

    # Statutory Applicability
    is_statutory = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)

    # Display & Ordering
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'name']
        ordering = ['display_order', 'name']
        verbose_name = 'Payhead Template'
        verbose_name_plural = 'Payhead Templates'

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.get_type_display()})"

    def clean(self):
        if not self.name:
            raise ValidationError('Payhead name is required.')

        # Validate unique name per client (case-insensitive)
        if PayheadTemplate.objects.filter(
                client=self.client,
                name__iexact=self.name
        ).exclude(pk=self.pk).exists():
            raise ValidationError(f'Payhead "{self.name}" already exists for this client.')

        # Validate formula if calculation type is FORMULA
        if self.calculation_type == 'FORMULA' and not self.formula:
            raise ValidationError('Formula is required for formula-based calculation.')

        # Validate default value range
        if self.default_value and self.max_value and self.default_value > self.max_value:
            raise ValidationError('Default value cannot exceed maximum value.')

        if self.default_value and self.min_value and self.default_value < self.min_value:
            raise ValidationError('Default value cannot be less than minimum value.')

    def calculate(self, basic_pay=None, gross_pay=None, attendance_days=None, units=None, variables=None):
        """Calculate the payhead value based on its calculation type"""
        if not basic_pay:
            basic_pay = 0
        if not gross_pay:
            gross_pay = 0
        if not attendance_days:
            attendance_days = 0
        if not units:
            units = 0
        if not variables:
            variables = {}

        # Add standard variables
        variables.update({
            'basic_pay': basic_pay,
            'gross_pay': gross_pay,
            'attendance_days': attendance_days,
            'units': units,
        })

        if self.calculation_type == 'FIXED':
            return float(self.default_value or 0)

        elif self.calculation_type == 'PERCENTAGE':
            return (float(self.default_value or 0) / 100) * basic_pay

        elif self.calculation_type == 'PERCENTAGE_GROSS':
            return (float(self.default_value or 0) / 100) * gross_pay

        elif self.calculation_type == 'PER_DAY':
            return (float(self.default_value or 0)) * attendance_days

        elif self.calculation_type == 'PER_UNIT':
            return (float(self.default_value or 0)) * units

        elif self.calculation_type == 'FORMULA':
            try:
                # Safely evaluate the formula
                allowed_names = {
                    'basic_pay': basic_pay,
                    'gross_pay': gross_pay,
                    'attendance_days': attendance_days,
                    'units': units,
                    **variables
                }
                # Use a safer evaluation method
                import ast
                import operator as op

                # Define allowed operators
                allowed_operators = {
                    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                    ast.Div: op.truediv, ast.FloorDiv: op.floordiv,
                    ast.Mod: op.mod, ast.Pow: op.pow,
                    ast.USub: op.neg, ast.UAdd: op.pos,
                }

                def eval_expr(node):
                    if isinstance(node, ast.Constant):
                        return node.value
                    elif isinstance(node, ast.Name):
                        if node.id in allowed_names:
                            return allowed_names[node.id]
                        else:
                            raise ValueError(f"Variable '{node.id}' not allowed")
                    elif isinstance(node, ast.BinOp):
                        op_func = allowed_operators.get(type(node.op))
                        if not op_func:
                            raise ValueError(f"Operator {type(node.op).__name__} not allowed")
                        return op_func(eval_expr(node.left), eval_expr(node.right))
                    elif isinstance(node, ast.UnaryOp):
                        op_func = allowed_operators.get(type(node.op))
                        if not op_func:
                            raise ValueError(f"Operator {type(node.op).__name__} not allowed")
                        return op_func(eval_expr(node.operand))
                    else:
                        raise ValueError(f"Expression type {type(node).__name__} not allowed")

                tree = ast.parse(self.formula, mode='eval')
                result = eval_expr(tree.body)
                return float(result)

            except Exception as e:
                # If formula fails, return default value
                print(f"Formula calculation error: {e}")
                return float(self.default_value or 0)

        return float(self.default_value or 0)


class AssignmentPayheadOverride(models.Model):
    """Employee-specific override for a client payhead"""

    assignment = models.ForeignKey('employees.EmployeeAssignment', on_delete=models.CASCADE,
                                   related_name='payhead_overrides')
    payhead_template = models.ForeignKey(PayheadTemplate, on_delete=models.CASCADE, related_name='overrides')

    # Override values
    overridden_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    # Reason for override
    reason = models.TextField(blank=True)

    # Audit
    overridden_at = models.DateTimeField(auto_now_add=True)
    overridden_by = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['assignment', 'payhead_template']
        ordering = ['payhead_template__display_order']
        verbose_name = 'Assignment Payhead Override'
        verbose_name_plural = 'Assignment Payhead Overrides'

    def __str__(self):
        return f"{self.assignment} - {self.payhead_template.name} Override"

    def get_effective_value(self, basic_pay=None, gross_pay=None, attendance_days=None, units=None, variables=None):
        """Get the effective value (either override or calculated from template)"""
        if self.overridden_value is not None:
            return float(self.overridden_value)
        return self.payhead_template.calculate(basic_pay, gross_pay, attendance_days, units, variables)


from django.db import models

# Create your models here.
