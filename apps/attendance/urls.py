# apps/attendance/urls.py
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Voucher CRUD
    path('', views.attendance_voucher_list, name='attendance_voucher_list'),
    path('create/', views.attendance_voucher_create, name='attendance_voucher_create'),
    path('<int:pk>/', views.attendance_voucher_detail, name='attendance_voucher_detail'),
    path('<int:pk>/edit/', views.attendance_voucher_edit, name='attendance_voucher_edit'),
    path('<int:pk>/delete/', views.attendance_voucher_delete, name='attendance_voucher_delete'),
    path('<int:pk>/finalize/', views.attendance_voucher_finalize, name='attendance_voucher_finalize'),

    # Details
    path('detail/<int:pk>/delete/', views.attendance_detail_delete, name='attendance_detail_delete'),

    # Import/Export
    path('<int:pk>/import/', views.attendance_import_excel, name='attendance_voucher_import'),
    path('<int:pk>/export/', views.attendance_export_excel, name='attendance_export_excel'),
    path('download-template/', views.attendance_download_template, name='attendance_download_template'),
]