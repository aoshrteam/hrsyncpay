# apps/payroll/urls.py
from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Payroll Runs
    path('', views.payroll_run_list, name='run_list'),
    path('create/', views.payroll_run_create, name='run_create'),
    path('<int:pk>/', views.payroll_run_detail, name='run_detail'),
    path('<int:pk>/process/', views.payroll_run_process, name='run_process'),
    path('<int:pk>/finalize/', views.payroll_run_finalize, name='run_finalize'),
    path('<int:pk>/delete/', views.payroll_run_delete, name='run_delete'),

    # Payslips
    path('payslip/<int:pk>/', views.payslip_detail, name='payslip_detail'),
    path('payslip/<int:pk>/pdf/', views.payslip_pdf, name='payslip_pdf'),

    # Payment Vouchers
    path('payments/', views.payment_voucher_list, name='payment_voucher_list'),
    path('payments/create/', views.payment_voucher_create, name='payment_voucher_create'),
    path('payments/confirm/', views.payment_voucher_confirm, name='payment_voucher_confirm'),
    path('payments/<int:pk>/', views.payment_voucher_detail, name='payment_voucher_detail'),
    path('payments/<int:pk>/approve/', views.payment_voucher_approve, name='payment_voucher_approve'),
    path('payments/<int:pk>/cancel/', views.payment_voucher_cancel, name='payment_voucher_cancel'),
]