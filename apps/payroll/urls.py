# apps/payroll/urls.py
from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Payroll Runs
    path('', views.run_list, name='run_list'),
    path('create/', views.run_create, name='run_create'),
    path('<int:pk>/', views.run_detail, name='run_detail'),
    path('<int:pk>/process/', views.run_process, name='run_process'),
    path('<int:pk>/finalize/', views.run_finalize, name='run_finalize'),
    path('<int:pk>/delete/', views.run_delete, name='run_delete'),
    path('<int:pk>/cancel/', views.run_cancel, name='run_cancel'),

    # Payslips
    path('payslip/<int:pk>/', views.payslip_detail, name='payslip_detail'),
    path('payslip/<int:pk>/pdf/', views.payslip_pdf, name='payslip_pdf'),

    # Payment Vouchers
    path('payments/', views.payment_voucher_list, name='payment_voucher_list'),
    path('payments/create/', views.payment_voucher_create, name='payment_voucher_create'),
    path('payments/<int:pk>/', views.payment_voucher_detail, name='payment_voucher_detail'),
    path('payments/<int:pk>/approve/', views.payment_voucher_approve, name='payment_voucher_approve'),
    path('payments/<int:pk>/cancel/', views.payment_voucher_cancel, name='payment_voucher_cancel'),

    # Salary Sheet
    path('salary-sheet/', views.salary_sheet, name='salary_sheet'),
    path('salary-sheet/generate/', views.salary_sheet_generate, name='salary_sheet_generate'),
    path('salary-sheet/client/<int:client_id>/', views.salary_sheet_generate_client,
         name='salary_sheet_generate_client'),
    path('salary-sheet/export/<int:client_id>/', views.salary_sheet_export, name='salary_sheet_export'),

    # Employee Ledger
    path('ledger/', views.employee_ledger, name='employee_ledger'),
    path('ledger/<int:employee_id>/', views.employee_ledger, name='employee_ledger_detail'),
]