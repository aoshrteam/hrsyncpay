# apps/core/context_processors.py
from django.utils import timezone


def breadcrumb_context(request):
    """Add breadcrumb and navigation context to all templates"""
    return {
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
        'current_user': request.user if request.user.is_authenticated else None,
    }


def navigation_history(request):
    """Store navigation history in session for back navigation"""
    if request.method == 'GET' and request.user.is_authenticated:
        current_path = request.path
        history = request.session.get('navigation_history', [])

        # Don't add if same as last
        if not history or history[-1] != current_path:
            history.append(current_path)

        # Keep last 15 items
        if len(history) > 15:
            history = history[-15:]

        request.session['navigation_history'] = history