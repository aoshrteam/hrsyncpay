# apps/leave/urls.py
from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    # ============================================
    # LEAVE TYPE URLs
    # ============================================
    path('types/', views.leave_type_list, name='leave_type_list'),
    path('types/create/', views.leave_type_create, name='leave_type_create'),
    path('types/<int:pk>/edit/', views.leave_type_edit, name='leave_type_edit'),
    path('types/<int:pk>/delete/', views.leave_type_delete, name='leave_type_delete'),

    # ============================================
    # EMPLOYEE LEAVE URLs
    # ============================================
    path('', views.leave_list, name='leave_list'),
    path('create/', views.leave_create, name='leave_create'),
    path('<int:pk>/', views.leave_detail, name='leave_detail'),
    path('<int:pk>/edit/', views.leave_edit, name='leave_edit'),
    path('<int:pk>/delete/', views.leave_delete, name='leave_delete'),
    path('<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('<int:pk>/cancel/', views.leave_cancel, name='leave_cancel'),

    # ============================================
    # LEAVE BALANCE URLs
    # ============================================
    path('balance/<int:employee_id>/', views.leave_balance, name='leave_balance'),
]