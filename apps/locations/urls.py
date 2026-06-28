# apps/locations/urls.py
from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    # Location Management
    path('', views.location_list, name='location_list'),
    path('client/<int:client_id>/', views.location_list_by_client, name='location_list_by_client'),
    path('create/', views.location_create, name='location_create'),
    path('create/client/<int:client_id>/', views.location_create_for_client, name='location_create_for_client'),
    path('<int:pk>/', views.location_detail, name='location_detail'),
    path('<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('<int:pk>/delete/', views.location_delete, name='location_delete'),
    path('<int:pk>/toggle/', views.location_toggle_status, name='location_toggle_status'),

    # Employee Mapping
    path('<int:pk>/employees/', views.location_employees, name='location_employees'),
    path('<int:pk>/employees/add/', views.location_employee_add, name='location_employee_add'),
    path('mapping/<int:pk>/edit/', views.location_employee_edit, name='location_employee_edit'),
    path('mapping/<int:pk>/delete/', views.location_employee_delete, name='location_employee_delete'),

    # API
    path('api/client-locations/', views.get_client_locations, name='get_client_locations'),
    path('api/<int:pk>/', views.get_location_details, name='get_location_details'),
]