# apps/statutory/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import StatutorySettings, ProfessionalTaxSlab, PFChallan, ESIChallan, PTChallan
from .forms import StatutorySettingsForm, ProfessionalTaxSlabForm


# ============================================
# STATUTORY SETTINGS
# ============================================

@login_required
def statutory_settings(request):
    """Statutory Settings View"""
    settings, created = StatutorySettings.objects.get_or_create(id=1)

    if request.method == 'POST':
        form = StatutorySettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.updated_by = request.user
            settings.save()
            messages.success(request, 'Statutory settings updated successfully!')
            return redirect('statutory:statutory_settings')
    else:
        form = StatutorySettingsForm(instance=settings)

    context = {
        'form': form,
        'settings': settings,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Statutory Settings', 'active': True},
        ],
    }
    return render(request, 'statutory/settings.html', context)


# ============================================
# PROFESSIONAL TAX SLABS
# ============================================

@login_required
def pt_slab_list(request):
    """Professional Tax Slab List"""
    slabs = ProfessionalTaxSlab.objects.all().order_by('state', 'min_amount')

    search = request.GET.get('search')
    if search:
        slabs = slabs.filter(state__icontains=search)

    paginator = Paginator(slabs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_slabs': slabs.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Statutory Settings', 'url': '/statutory/settings/', 'active': False},
            {'name': 'PT Slabs', 'active': True},
        ],
    }
    return render(request, 'statutory/pt_slab_list.html', context)


@login_required
@transaction.atomic
def pt_slab_create(request):
    """Create Professional Tax Slab"""
    if request.method == 'POST':
        form = ProfessionalTaxSlabForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'PT Slab created successfully!')
            return redirect('statutory:pt_slab_list')
    else:
        form = ProfessionalTaxSlabForm()

    context = {
        'form': form,
        'title': 'Create PT Slab',
        'button_text': 'Save Slab',
    }
    return render(request, 'statutory/pt_slab_form.html', context)


@login_required
@transaction.atomic
def pt_slab_edit(request, pk):
    """Edit Professional Tax Slab"""
    slab = get_object_or_404(ProfessionalTaxSlab, pk=pk)

    if request.method == 'POST':
        form = ProfessionalTaxSlabForm(request.POST, instance=slab)
        if form.is_valid():
            form.save()
            messages.success(request, 'PT Slab updated successfully!')
            return redirect('statutory:pt_slab_list')
    else:
        form = ProfessionalTaxSlabForm(instance=slab)

    context = {
        'form': form,
        'slab': slab,
        'title': 'Edit PT Slab',
        'button_text': 'Update Slab',
    }
    return render(request, 'statutory/pt_slab_form.html', context)


@login_required
@transaction.atomic
def pt_slab_delete(request, pk):
    """Delete Professional Tax Slab"""
    slab = get_object_or_404(ProfessionalTaxSlab, pk=pk)

    if request.method == 'POST':
        slab.delete()
        messages.success(request, 'PT Slab deleted successfully!')
        return redirect('statutory:pt_slab_list')

    context = {
        'slab': slab,
    }
    return render(request, 'statutory/pt_slab_confirm_delete.html', context)


from django.shortcuts import render

# Create your views here.
