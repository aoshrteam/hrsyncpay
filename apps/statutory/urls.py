# apps/statutory/urls.py
from django.urls import path
from . import views

app_name = 'statutory'

urlpatterns = [
    # Statutory Settings
    path('settings/', views.statutory_settings, name='statutory_settings'),

    # Professional Tax Slabs
    path('pt-slabs/', views.pt_slab_list, name='pt_slab_list'),
    path('pt-slabs/create/', views.pt_slab_create, name='pt_slab_create'),
    path('pt-slabs/<int:pk>/edit/', views.pt_slab_edit, name='pt_slab_edit'),
    path('pt-slabs/<int:pk>/delete/', views.pt_slab_delete, name='pt_slab_delete'),
]