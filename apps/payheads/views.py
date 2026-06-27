# apps/payheads/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import PayheadCategory, PayheadTemplate, AssignmentPayheadOverride
from .forms import PayheadCategoryForm, PayheadTemplateForm, AssignmentPayheadOverrideForm
from apps.clients.models import Client
from apps.core.decorators import data_entry_or_admin_required


# ============================================
# PAYHEAD VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def payhead_list(request, client_id=None):
    """List payhead templates for a client"""
    if client_id:
        client = get_object_or_404(Client, pk=client_id)
        payheads = PayheadTemplate.objects.filter(client=client, is_active=True)
    else:
        client = None
        payheads = PayheadTemplate.objects.filter(is_active=True)

    # Group by type
    earnings = payheads.filter(type='EARNING')
    deductions = payheads.filter(type='DEDUCTION')
    reimbursements = payheads.filter(type='REIMBURSEMENT')
    bonuses = payheads.filter(type='BONUS')
    allowances = payheads.filter(type='ALLOWANCE')
    others = payheads.filter(type='OTHER')

    context = {
        'client': client,
        'payheads': payheads,
        'earnings': earnings,
        'deductions': deductions,
        'reimbursements': reimbursements,
        'bonuses': bonuses,
        'allowances': allowances,
        'others': others,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payhead Management', 'active': True},
        ],
    }
    return render(request, 'payheads/payhead_list.html', context)


@login_required
@data_entry_or_admin_required
def payhead_create(request, client_id=None):
    """Create a new payhead template"""
    client = None
    if client_id:
        client = get_object_or_404(Client, pk=client_id)

    if request.method == 'POST':
        form = PayheadTemplateForm(request.POST)
        if form.is_valid():
            payhead = form.save()
            messages.success(request, f'Payhead "{payhead.name}" created successfully!')
            return redirect('payheads:payhead_list')
    else:
        initial = {}
        if client:
            initial['client'] = client.id
        form = PayheadTemplateForm(initial=initial)
        if client:
            form.fields['category'].queryset = PayheadCategory.objects.filter(client=client, is_active=True)

    context = {
        'form': form,
        'client': client,
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
    """Edit a payhead template"""
    payhead = get_object_or_404(PayheadTemplate, pk=pk)

    if request.method == 'POST':
        form = PayheadTemplateForm(request.POST, instance=payhead)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payhead "{payhead.name}" updated successfully!')
            return redirect('payheads:payhead_list')
    else:
        form = PayheadTemplateForm(instance=payhead)
        form.fields['category'].queryset = PayheadCategory.objects.filter(client=payhead.client, is_active=True)

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
    """Delete a payhead template (soft delete)"""
    payhead = get_object_or_404(PayheadTemplate, pk=pk)

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


# ============================================
# CATEGORY VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def category_list(request, client_id=None):
    """List payhead categories for a client"""
    if client_id:
        client = get_object_or_404(Client, pk=client_id)
        categories = PayheadCategory.objects.filter(client=client)
    else:
        client = None
        categories = PayheadCategory.objects.all()

    context = {
        'client': client,
        'categories': categories,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Categories', 'active': True},
        ],
    }
    return render(request, 'payheads/category_list.html', context)


@login_required
@data_entry_or_admin_required
def category_create(request, client_id=None):
    """Create a new payhead category"""
    client = None
    if client_id:
        client = get_object_or_404(Client, pk=client_id)

    if request.method == 'POST':
        form = PayheadCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('payheads:category_list')
    else:
        initial = {}
        if client:
            initial['client'] = client.id
        form = PayheadCategoryForm(initial=initial)

    context = {
        'form': form,
        'client': client,
        'title': 'Create Category',
        'button_text': 'Create Category',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Categories', 'url': '/payheads/categories/', 'active': False},
            {'name': 'Create Category', 'active': True},
        ],
    }
    return render(request, 'payheads/category_form.html', context)


@login_required
@data_entry_or_admin_required
def category_edit(request, pk):
    """Edit a payhead category"""
    category = get_object_or_404(PayheadCategory, pk=pk)

    if request.method == 'POST':
        form = PayheadCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('payheads:category_list')
    else:
        form = PayheadCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'button_text': 'Update Category',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Categories', 'url': '/payheads/categories/', 'active': False},
            {'name': f'Edit {category.name}', 'active': True},
        ],
    }
    return render(request, 'payheads/category_form.html', context)


@login_required
@data_entry_or_admin_required
def category_delete(request, pk):
    """Delete a payhead category"""
    category = get_object_or_404(PayheadCategory, pk=pk)

    if request.method == 'POST':
        category.is_active = False
        category.save()
        messages.success(request, f'Category "{category.name}" deleted successfully!')
        return redirect('payheads:category_list')

    context = {
        'category': category,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Payheads', 'url': '/payheads/', 'active': False},
            {'name': 'Categories', 'url': '/payheads/categories/', 'active': False},
            {'name': f'Delete {category.name}', 'active': True},
        ],
    }
    return render(request, 'payheads/category_confirm_delete.html', context)


# ============================================
# API VIEWS
# ============================================

@login_required
def get_client_payheads(request):
    """API endpoint to get payheads for a client (AJAX)"""
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'error': 'Client ID required'}, status=400)

    try:
        client = Client.objects.get(pk=client_id)
        payheads = PayheadTemplate.objects.filter(client=client, is_active=True)

        data = {
            'earnings': [],
            'deductions': [],
            'reimbursements': [],
            'bonuses': [],
            'allowances': [],
            'others': [],
        }

        for payhead in payheads:
            item = {
                'id': payhead.id,
                'name': payhead.name,
                'code': payhead.code,
                'type': payhead.type,
                'calculation_type': payhead.calculation_type,
                'default_value': str(payhead.default_value),
                'description': payhead.description,
            }

            if payhead.type == 'EARNING':
                data['earnings'].append(item)
            elif payhead.type == 'DEDUCTION':
                data['deductions'].append(item)
            elif payhead.type == 'REIMBURSEMENT':
                data['reimbursements'].append(item)
            elif payhead.type == 'BONUS':
                data['bonuses'].append(item)
            elif payhead.type == 'ALLOWANCE':
                data['allowances'].append(item)
            else:
                data['others'].append(item)

        return JsonResponse(data)

    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)


@login_required
def get_client_categories(request):
    """API endpoint to get categories for a client (AJAX)"""
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'error': 'Client ID required'}, status=400)

    try:
        client = Client.objects.get(pk=client_id)
        categories = PayheadCategory.objects.filter(client=client, is_active=True)

        data = {
            'categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'type': cat.category_type,
                    'display_name': f"{cat.name} ({cat.get_category_type_display()})"
                }
                for cat in categories
            ]
        }
        return JsonResponse(data)

    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)


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