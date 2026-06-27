# apps/employees/forms.py - Complete Fixed
from django import forms
from django.core.exceptions import ValidationError
from .models import Employee, EmployeeDocument, EmployeeAssignment
from apps.clients.models import Client
import json





from django.test import TestCase

# Create your tests here.
