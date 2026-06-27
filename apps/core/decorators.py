# apps/core/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator to check if user is admin or superuser"""

    @login_required
    def wrapper(request, *args, **kwargs):
        # ✅ Superuser or Admin को allow करें
        if request.user.is_superuser or request.user.role == 'ADMIN':
            return view_func(request, *args, **kwargs)

        messages.error(request, 'You do not have permission to access this page. Admin access required.')
        return redirect('core:dashboard')

    return wrapper


def data_entry_or_admin_required(view_func):
    """Decorator to check if user is data entry or admin or superuser"""

    @login_required
    def wrapper(request, *args, **kwargs):
        # ✅ Superuser, Admin, Data Entry को allow करें
        if request.user.is_superuser or request.user.role in ['ADMIN', 'DATA_ENTRY']:
            return view_func(request, *args, **kwargs)

        messages.error(request,
                       f'You do not have permission to access this page. Your role: {request.user.role}. Required: ADMIN or DATA_ENTRY')
        return redirect('core:dashboard')

    return wrapper