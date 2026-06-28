# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ==========================================
    # DASHBOARD
    # ==========================================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ==========================================
    # IMPORT/EXPORT
    # ==========================================
    path('import-export/', views.import_export_home, name='import_export'),
    path('import-employees/', views.import_employees, name='import_employees'),
    path('import-clients/', views.import_clients, name='import_clients'),
    path('export-employees/', views.export_employees, name='export_employees'),
    path('export-clients/', views.export_clients, name='export_clients'),
    path('export-import-errors/', views.export_import_errors, name='export_import_errors'),
    path('download-employee-sample/', views.download_employee_sample, name='download_employee_sample'),
    path('download-client-sample/', views.download_client_sample, name='download_client_sample'),

    # ==========================================
    # NOTIFICATIONS
    # ==========================================
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),

    # ==========================================
    # USER PROFILE
    # ==========================================
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.user_profile_edit, name='user_profile_edit'),
    path('profile/change-password/', views.user_change_password, name='user_change_password'),

    # ==========================================
    # SETTINGS
    # ==========================================
    path('settings/', views.app_settings, name='app_settings'),
    path('settings/update/', views.app_settings_update, name='app_settings_update'),

    # ==========================================
    # AUDIT LOG
    # ==========================================
    path('audit-log/', views.audit_log, name='audit_log'),

    # ==========================================
    # REPORTS
    # ==========================================
    path('reports/', views.reports, name='reports'),
    path('reports/payroll/', views.report_payroll, name='report_payroll'),
    path('reports/employee/', views.report_employee, name='report_employee'),
    path('reports/client/', views.report_client, name='report_client'),
    path('client-wise-summary/', views.client_wise_summary, name='client_wise_summary'),
    path('pending-payments-summary/', views.pending_payments_summary, name='pending_payments_summary'),

    # ==========================================
    # API ENDPOINTS (AJAX)
    # ==========================================
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),

    # ==========================================
    # BACK NAVIGATION
    # ==========================================
    path('back/', views.back_navigation, name='back_navigation'),
    path('clear-import-errors/', views.clear_import_errors, name='clear_import_errors'),
    path('export-import-errors/', views.export_import_errors, name='export_import_errors'),
    path('import-assignments/', views.import_assignments, name='import_assignments'),
    path('download-assignment-sample/', views.download_assignment_sample, name='download_assignment_sample'),
]