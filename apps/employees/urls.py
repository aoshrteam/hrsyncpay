# apps/employees/urls.py
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # ==========================================
    # EMPLOYEE MANAGEMENT
    # ==========================================
    # List employees
    path('', views.employee_list, name='employee_list'),

    # Create employee
    path('create/', views.employee_create, name='employee_create'),

    # Employee detail
    path('<int:pk>/', views.employee_detail, name='employee_detail'),

    # Edit employee
    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),

    # Delete employee
    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Employee profile (alternate view)
    path('<int:pk>/profile/', views.employee_profile, name='employee_profile'),

    # ==========================================
    # EMPLOYEE DOCUMENTS
    # ==========================================
    # List documents
    path('<int:pk>/documents/', views.employee_documents, name='employee_documents'),

    # Upload document
    path('<int:pk>/documents/upload/', views.document_upload, name='document_upload'),

    # Delete document
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),

    # Download document
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),

    # Verify document
    path('documents/<int:pk>/verify/', views.document_verify, name='document_verify'),

    # ==========================================
    # EMPLOYEE ASSIGNMENTS
    # ==========================================
    # List assignments
    path('<int:pk>/assignments/', views.employee_assignments, name='employee_assignments'),

    # Create assignment
    path('<int:pk>/assignments/create/', views.assignment_create, name='assignment_create'),

    # Edit assignment
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),

    # Delete assignment
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),

    # View assignment details
    path('assignments/<int:pk>/view/', views.assignment_detail, name='assignment_detail'),

    # ==========================================
    # SERVICE HISTORY
    # ==========================================
    # Employee service history
    path('<int:pk>/service-history/', views.service_history, name='service_history'),

    # ==========================================
    # IMPORT/EXPORT
    # ==========================================
    # Import employees
    path('import/', views.employee_import, name='employee_import'),

    # Export employees
    path('export/', views.employee_export, name='employee_export'),

    # Download sample template
    path('sample/', views.employee_import_sample, name='employee_import_sample'),

    # ==========================================
    # BULK OPERATIONS
    # ==========================================
    # Bulk delete
    path('bulk-delete/', views.employee_bulk_delete, name='employee_bulk_delete'),

    # Bulk update status
    path('bulk-update-status/', views.employee_bulk_update_status, name='employee_bulk_update_status'),

    # ==========================================
    # REPORTS
    # ==========================================
    # Employee list report
    path('report/list/', views.employee_list_report, name='employee_list_report'),

    # Employee statistics
    path('report/statistics/', views.employee_statistics, name='employee_statistics'),

    # ==========================================
    # API ENDPOINTS (AJAX)
    # ==========================================
    # Search employees (JSON)
    path('api/search/', views.employee_search, name='employee_search'),

    # Get employee details (JSON)
    path('api/<int:pk>/', views.get_employee_details, name='get_employee_details'),

    # Get employee assignments (JSON)
    path('api/<int:pk>/assignments/', views.get_employee_assignments, name='get_employee_assignments'),
# ✅ Employee Assignments
    path('<int:pk>/assignments/', views.employee_assignments, name='employee_assignments'),
    path('<int:pk>/assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),

# Bulk Delete
    path('bulk-delete/', views.employee_bulk_delete, name='employee_bulk_delete'),
    path('bulk-delete-all/', views.employee_bulk_delete_all, name='employee_bulk_delete_all'),
]