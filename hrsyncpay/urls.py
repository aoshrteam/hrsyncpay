# hrsyncpay/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='core:dashboard', permanent=False)),

    # Core App
    path('', include('apps.core.urls')),

    # Business Apps
    path('employees/', include('apps.employees.urls')),
    path('clients/', include('apps.clients.urls')),
    path('company/', include('apps.company.urls')),
    path('payheads/', include('apps.payheads.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('payroll/', include('apps.payroll.urls')),
    path('leave/', include('apps.leave.urls')),
    path('loans/', include('apps.loans.urls')),
    path('statutory/', include('apps.statutory.urls')),

    # Accounts App
    path('accounts/', include('apps.accounts.urls')),  # ✅ ADD THIS LINE

    # Django Authentication
    path('auth/', include('django.contrib.auth.urls')),  # ✅ For login/logout
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)