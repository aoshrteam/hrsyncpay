# apps/payheads/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Payhead  # ✅ Only Payhead model (Global)
from .forms import PayheadForm  # ✅ Global Payhead Form
from apps.clients.models import Client
from apps.core.decorators import data_entry_or_admin_required


# ============================================
# PAYHEAD VIEWS - GLOBAL
# ============================================

@login_required
@data_entry_or_admin_required
def payhead_list(request):
    """List all global payheads"""
    payheads = Payhead.objects.filter(is_active=True).order_by('type', 'display_order', 'name')

    # Group by type
    earnings = payheads.filter(type='EARNING')
    deductions = payheads.filter(type='DEDUCTION')
    statutory = payheads.filter(type='STATUTORY_DEDUCTION')
    reimbursements = payheads.filter(type='REIMBURSEMENT')
    loans = payheads.filter(type='LOAN')
    bonuses = payheads.filter(type='BONUS')
    allowances = payheads.filter(type='ALLOWANCE')
    others = payheads.exclude(
        type__in=['EARNING', 'DEDUCTION', 'STATUTORY_DEDUCTION', 'REIMBURSEMENT', 'LOAN', 'BONUS', 'ALLOWANCE']
    )

    context = {
        'payheads': payheads,
        'earnings': earnings,
        'deductions': deductions,
        'statutory': statutory,
        'reimbursements': reimbursements,
        'loans': loans,
        'bonuses': bonuses,
        'allowances': allowances,
        'others': others,
        'total_count': payheads.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payhead Management', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_list.html', context)


@login_required
@data_entry_or_admin_required
def payhead_create(request):
    """Create a new global payhead"""
    if request.method == 'POST':
        form = PayheadForm(request.POST)
        if form.is_valid():
            payhead = form.save()
            messages.success(request, f'Payhead "{payhead.name}" created successfully!')
            return redirect('payheads:payhead_list')
    else:
        form = PayheadForm()

    context = {
        'form': form,
        'title': 'Create Payhead',
        'button_text': 'Create Payhead',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payhead Management', 'url': '/payheads/', 'active': False},
            {'name': 'Create Payhead', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_form.html', context)


@login_required
@data_entry_or_admin_required
def payhead_edit(request, pk):
    """Edit a global payhead"""
    payhead = get_object_or_404(Payhead, pk=pk)

    if request.method == 'POST':
        form = PayheadForm(request.POST, instance=payhead)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payhead "{payhead.name}" updated successfully!')
            return redirect('payheads:payhead_list')
    else:
        form = PayheadForm(instance=payhead)

    context = {
        'form': form,
        'payhead': payhead,
        'title': 'Edit Payhead',
        'button_text': 'Update Payhead',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': f'Edit {payhead.name}', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_form.html', context)


@login_required
@data_entry_or_admin_required
def payhead_delete(request, pk):
    """Delete a global payhead (soft delete)"""
    payhead = get_object_or_404(Payhead, pk=pk)

    if request.method == 'POST':
        payhead.is_active = False
        payhead.save()
        messages.success(request, f'Payhead "{payhead.name}" deleted successfully!')
        return redirect('payheads:payhead_list')

    context = {
        'payhead': payhead,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': f'Delete {payhead.name}', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_confirm_delete.html', context)


@login_required
@data_entry_or_admin_required
def payhead_toggle_status(request, pk):
    """Toggle payhead active status"""
    payhead = get_object_or_404(Payhead, pk=pk)
    payhead.is_active = not payhead.is_active
    payhead.save()
    status = 'activated' if payhead.is_active else 'deactivated'
    messages.success(request, f'Payhead "{payhead.name}" {status}!')
    return redirect('payheads:payhead_list')


# ============================================
# API VIEWS
# ============================================

@login_required
def get_payhead_types(request):
    """API endpoint to get all payhead types"""
    from apps.core.import_export import ImportExportService
    types = ImportExportService.get_payhead_type_choices()
    return JsonResponse({'types': types})


@login_required
def get_all_payheads(request):
    """API endpoint to get all global payheads (AJAX)"""
    payheads = Payhead.objects.filter(is_active=True).order_by('type', 'name')

    data = {
        'payheads': [
            {
                'id': p.id,
                'name': p.name,
                'type': p.type,
                'type_display': p.get_type_display(),
                'code': p.code,
                'description': p.description,
                'display_order': p.display_order,
            }
            for p in payheads
        ]
    }
    return JsonResponse(data)


# ============================================
# DUMMY VIEWS (To prevent reverse errors)
# ============================================

@login_required
def payhead_import(request):
    """Import Payheads from Excel (Coming Soon)"""
    messages.info(request, 'Payhead import functionality coming soon!')
    return redirect('payheads:payhead_list')


@login_required
def payhead_export(request):
    """Export Payheads to Excel (Coming Soon)"""
    messages.info(request, 'Payhead export functionality coming soon!')
    return redirect('payheads:payhead_list')


@login_required
def payhead_sample(request):
    """Download Payhead Import Sample Template (Coming Soon)"""
    messages.info(request, 'Payhead sample download coming soon!')
    return redirect('payheads:payhead_list')


@login_required
def payhead_summary_report(request):
    """Payhead Summary Report (Coming Soon)"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Summary Report', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_summary_report.html', context)


@login_required
def payhead_usage_report(request):
    """Payhead Usage Report (Coming Soon)"""
    context = {
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Usage Report', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_usage_report.html', context)