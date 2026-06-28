# apps/attendance/urls.py
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Voucher Management
    path('', views.attendance_voucher_list, name='attendance_voucher_list'),
    path('create/', views.attendance_voucher_create, name='attendance_voucher_create'),
    path('<int:pk>/', views.attendance_voucher_detail, name='attendance_voucher_detail'),
    path('<int:pk>/edit/', views.attendance_voucher_edit, name='attendance_voucher_edit'),
    path('<int:pk>/delete/', views.attendance_voucher_delete, name='attendance_voucher_delete'),

    # Bulk Delete
    path('<int:pk>/bulk-delete/', views.attendance_voucher_bulk_delete, name='attendance_voucher_bulk_delete'),
    path('<int:pk>/bulk-delete-all/', views.attendance_voucher_bulk_delete_all,
         name='attendance_voucher_bulk_delete_all'),

    # Detail Management
    path('detail/<int:pk>/edit/', views.attendance_detail_edit, name='attendance_detail_edit'),
    path('detail/<int:pk>/delete/', views.attendance_detail_delete, name='attendance_detail_delete'),

    # Import
    path('<int:pk>/import/', views.attendance_import, name='attendance_import'),
    path('download-template/', views.attendance_download_template, name='attendance_download_template'),
]