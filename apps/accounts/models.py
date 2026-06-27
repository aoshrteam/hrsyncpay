# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DATA_ENTRY', 'Data Entry'),
        ('VIEWER', 'Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    phone = models.CharField(max_length=15, blank=True)
    employee_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_data_entry(self):
        return self.role in ['ADMIN', 'DATA_ENTRY']

    def is_viewer(self):
        return self.role == 'VIEWER'

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'accounts_user'