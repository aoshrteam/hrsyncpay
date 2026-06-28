# apps/payheads/models.py
from django.db import models


class Payhead(models.Model):
    """Global Fixed Payhead - Same for all clients"""

    PAYHEAD_TYPES = [
        ('EARNING', '💚 Earning'),
        ('DEDUCTION', '❤️ Deduction'),
        ('STATUTORY_DEDUCTION', '🧡 Statutory Deduction'),
        ('REIMBURSEMENT', '💙 Reimbursement'),
        ('LOAN', '💜 Loan'),
        ('BONUS', '💛 Bonus'),
        ('ALLOWANCE', '🩵 Allowance'),
    ]

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=PAYHEAD_TYPES, default='EARNING')
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"

    def get_type_icon(self):
        icons = {
            'EARNING': '💚',
            'DEDUCTION': '❤️',
            'STATUTORY_DEDUCTION': '🧡',
            'REIMBURSEMENT': '💙',
            'LOAN': '💜',
            'BONUS': '💛',
            'ALLOWANCE': '🩵',
        }
        return icons.get(self.type, '⬜')

    class Meta:
        ordering = ['type', 'display_order', 'name']
        verbose_name = 'Payhead'
        verbose_name_plural = 'Payheads'