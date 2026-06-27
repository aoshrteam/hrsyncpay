# apps/loans/urls.py
from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    # Loan Types
    path('types/', views.loan_type_list, name='loan_type_list'),
    path('types/create/', views.loan_type_create, name='loan_type_create'),
    path('types/<int:pk>/edit/', views.loan_type_edit, name='loan_type_edit'),

    # Employee Loans
    path('', views.loan_list, name='loan_list'),
    path('create/', views.loan_create, name='loan_create'),
    path('<int:pk>/', views.loan_detail, name='loan_detail'),
    path('<int:pk>/edit/', views.loan_edit, name='loan_edit'),
    path('<int:pk>/delete/', views.loan_delete, name='loan_delete'),
    path('<int:pk>/pay/', views.loan_make_payment, name='loan_make_payment'),

    # Deductions
    path('deduction/<int:pk>/', views.loan_deduction_detail, name='loan_deduction_detail'),
]