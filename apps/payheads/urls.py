# apps/payheads/urls.py
from django.urls import path
from . import views

app_name = 'payheads'

urlpatterns = [
    # Payhead Management
    path('', views.payhead_list, name='payhead_list'),
    path('client/<int:client_id>/', views.payhead_list, name='payhead_list_by_client'),
    path('create/', views.payhead_create, name='payhead_create'),
    path('create/client/<int:client_id>/', views.payhead_create, name='payhead_create_for_client'),
    path('<int:pk>/edit/', views.payhead_edit, name='payhead_edit'),
    path('<int:pk>/delete/', views.payhead_delete, name='payhead_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/client/<int:client_id>/', views.category_list, name='category_list_by_client'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/create/client/<int:client_id>/', views.category_create, name='category_create_for_client'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Import/Export (Dummy)
    path('import/', views.payhead_import, name='payhead_import'),
    path('export/', views.payhead_export, name='payhead_export'),
    path('sample/', views.payhead_sample, name='payhead_sample'),

    # Reports (Dummy)
    path('report/summary/', views.payhead_summary_report, name='payhead_summary_report'),
    path('report/usage/', views.payhead_usage_report, name='payhead_usage_report'),

    # API
    path('api/client-payheads/', views.get_client_payheads, name='get_client_payheads'),
    path('api/client-categories/', views.get_client_categories, name='get_client_categories'),
]