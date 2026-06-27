# apps/company/urls.py
from django.urls import path
from . import views

app_name = 'company'

urlpatterns = [
    # Company CRUD
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('<int:pk>/', views.company_detail, name='company_detail'),
    path('<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Company Users
    path('<int:pk>/add-user/', views.company_add_user, name='company_add_user'),
    path('remove-user/<int:pk>/', views.company_remove_user, name='company_remove_user'),
]