# apps/payheads/urls.py
from django.urls import path
from . import views

app_name = 'payheads'

urlpatterns = [
    # Payhead Management
    path('', views.payhead_list, name='payhead_list'),
    path('create/', views.payhead_create, name='payhead_create'),
    path('<int:pk>/edit/', views.payhead_edit, name='payhead_edit'),
    path('<int:pk>/delete/', views.payhead_delete, name='payhead_delete'),
    path('<int:pk>/toggle/', views.payhead_toggle_status, name='payhead_toggle_status'),

    # ✅ REMOVE THESE LINES
    # path('categories/', views.category_list, name='category_list'),
    # path('categories/create/', views.category_create, name='category_create'),
    # path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    # path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # API
    path('api/payhead-types/', views.get_payhead_types, name='get_payhead_types'),
    path('api/all-payheads/', views.get_all_payheads, name='get_all_payheads'),

    # Dummy URLs
    path('import/', views.payhead_import, name='payhead_import'),
    path('export/', views.payhead_export, name='payhead_export'),
    path('sample/', views.payhead_sample, name='payhead_sample'),
    path('report/summary/', views.payhead_summary_report, name='payhead_summary_report'),
    path('report/usage/', views.payhead_usage_report, name='payhead_usage_report'),
]