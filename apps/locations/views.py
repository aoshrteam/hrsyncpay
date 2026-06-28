# apps/locations/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q
from .models import Location, LocationEmployeeMapping
from .forms import LocationForm, LocationEmployeeMappingForm
from apps.clients.models import Client
from apps.employees.models import Employee
from apps.core.decorators import data_entry_or_admin_required


# ============================================
# LOCATION LIST VIEWS
# ============================================

@login_required
def location_list(request):
    """List all locations"""
    locations = Location.objects.filter(is_active=True)

    search = request.GET.get('search')
    if search:
        locations = locations.filter(
            Q(location_name__icontains=search) |
            Q(location_code__icontains=search) |
            Q(client__name__icontains=search)
        )

    paginator = Paginator(locations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_locations': locations.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'active': True},
        ],
    }
    return render(request, 'locations/location_list.html', context)


@login_required
def location_list_by_client(request, client_id):
    """List locations for a specific client"""
    client = get_object_or_404(Client, pk=client_id)
    locations = client.locations.filter(is_active=True)

    context = {
        'client': client,
        'locations': locations,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Clients', 'url': '/clients/', 'active': False},
            {'name': client.name, 'url': f'/clients/{client.id}/', 'active': False},
            {'name': 'Locations', 'active': True},
        ],
    }
    return render(request, 'locations/location_list.html', context)


# ============================================
# LOCATION CREATE VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def location_create(request):
    """Create new location"""
    return location_create_for_client(request, client_id=None)


@login_required
@data_entry_or_admin_required
def location_create_for_client(request, client_id=None):
    """Create location for a specific client"""
    client = None
    if client_id:
        client = get_object_or_404(Client, pk=client_id)

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.location_name}" created successfully!')
            return redirect('locations:location_detail', pk=location.pk)
    else:
        initial = {}
        if client:
            initial['client'] = client.id
        form = LocationForm(initial=initial)

    context = {
        'form': form,
        'client': client,
        'title': 'Create Location',
        'button_text': 'Create Location',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': 'Create Location', 'active': True},
        ],
    }
    return render(request, 'locations/location_form.html', context)


# ============================================
# LOCATION DETAIL VIEWS
# ============================================

@login_required
def location_detail(request, pk):
    """Location detail view"""
    location = get_object_or_404(Location, pk=pk)
    employees = location.employee_mappings.filter(is_current=True)

    context = {
        'location': location,
        'employees': employees,
        'total_employees': employees.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': location.location_name, 'active': True},
        ],
    }
    return render(request, 'locations/location_detail.html', context)


# ============================================
# LOCATION EDIT VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def location_edit(request, pk):
    """Edit location"""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location "{location.location_name}" updated successfully!')
            return redirect('locations:location_detail', pk=location.pk)
    else:
        form = LocationForm(instance=location)

    context = {
        'form': form,
        'location': location,
        'title': 'Edit Location',
        'button_text': 'Update Location',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': location.location_name, 'url': f'/locations/{location.id}/', 'active': False},
            {'name': 'Edit', 'active': True},
        ],
    }
    return render(request, 'locations/location_form.html', context)


# ============================================
# LOCATION DELETE VIEWS
# ============================================

@login_required
@data_entry_or_admin_required
def location_delete(request, pk):
    """Soft delete location"""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        location.is_active = False
        location.save()
        messages.success(request, f'Location "{location.location_name}" deleted successfully!')
        return redirect('locations:location_list')

    context = {
        'location': location,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': f'Delete {location.location_name}', 'active': True},
        ],
    }
    return render(request, 'locations/location_confirm_delete.html', context)


# ============================================
# LOCATION TOGGLE STATUS
# ============================================

@login_required
@data_entry_or_admin_required
def location_toggle_status(request, pk):
    """Toggle location active status"""
    location = get_object_or_404(Location, pk=pk)
    location.is_active = not location.is_active
    location.save()
    status = 'activated' if location.is_active else 'deactivated'
    messages.success(request, f'Location "{location.location_name}" {status}!')
    return redirect('locations:location_detail', pk=location.pk)


# ============================================
# LOCATION EMPLOYEE MANAGEMENT
# ============================================

@login_required
def location_employees(request, pk):
    """List employees at a location"""
    location = get_object_or_404(Location, pk=pk)
    mappings = location.employee_mappings.all()

    context = {
        'location': location,
        'mappings': mappings,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': location.location_name, 'url': f'/locations/{location.id}/', 'active': False},
            {'name': 'Employees', 'active': True},
        ],
    }
    return render(request, 'locations/location_employees.html', context)


@login_required
@data_entry_or_admin_required
def location_employee_add(request, pk):
    """Add employee to location"""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        form = LocationEmployeeMappingForm(request.POST)
        if form.is_valid():
            mapping = form.save(commit=False)
            mapping.location = location
            mapping.save()
            messages.success(request, f'Employee assigned to location successfully!')
            return redirect('locations:location_employees', pk=location.pk)
    else:
        form = LocationEmployeeMappingForm(initial={'location': location})
        form.fields['employee'].queryset = Employee.objects.filter(is_active=True)

    context = {
        'form': form,
        'location': location,
        'title': 'Assign Employee',
        'button_text': 'Assign Employee',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': location.location_name, 'url': f'/locations/{location.id}/', 'active': False},
            {'name': 'Assign Employee', 'active': True},
        ],
    }
    return render(request, 'locations/location_employee_form.html', context)


@login_required
@data_entry_or_admin_required
def location_employee_edit(request, pk):
    """Edit employee-location mapping"""
    mapping = get_object_or_404(LocationEmployeeMapping, pk=pk)

    if request.method == 'POST':
        form = LocationEmployeeMappingForm(request.POST, instance=mapping)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mapping updated successfully!')
            return redirect('locations:location_employees', pk=mapping.location.pk)
    else:
        form = LocationEmployeeMappingForm(instance=mapping)

    context = {
        'form': form,
        'mapping': mapping,
        'title': 'Edit Mapping',
        'button_text': 'Update Mapping',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': mapping.location.location_name, 'url': f'/locations/{mapping.location.id}/', 'active': False},
            {'name': 'Edit Mapping', 'active': True},
        ],
    }
    return render(request, 'locations/location_employee_form.html', context)


@login_required
@data_entry_or_admin_required
def location_employee_delete(request, pk):
    """Delete employee-location mapping"""
    mapping = get_object_or_404(LocationEmployeeMapping, pk=pk)
    location_id = mapping.location.id

    if request.method == 'POST':
        mapping.delete()
        messages.success(request, 'Employee removed from location successfully!')
        return redirect('locations:location_employees', pk=location_id)

    context = {
        'mapping': mapping,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Locations', 'url': '/locations/', 'active': False},
            {'name': mapping.location.location_name, 'url': f'/locations/{mapping.location.id}/', 'active': False},
            {'name': 'Remove Employee', 'active': True},
        ],
    }
    return render(request, 'locations/location_employee_confirm_delete.html', context)


# ============================================
# API ENDPOINTS
# ============================================

@login_required
def get_client_locations(request):
    """API: Get locations for a client (AJAX)"""
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'error': 'Client ID required'}, status=400)

    try:
        client = Client.objects.get(pk=client_id)
        locations = client.locations.filter(is_active=True)

        data = {
            'locations': [
                {
                    'id': loc.id,
                    'code': loc.location_code,
                    'name': loc.location_name,
                    'display_name': loc.display_name,
                    'gst_number': loc.effective_gst,
                    'gst_state': loc.effective_gst_state,
                    'address': loc.full_address,
                }
                for loc in locations
            ]
        }
        return JsonResponse(data)

    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)


@login_required
def get_location_details(request, pk):
    """API: Get location details (AJAX)"""
    try:
        location = Location.objects.get(pk=pk)
        data = {
            'id': location.id,
            'client_id': location.client.id,
            'client_name': location.client.name,
            'code': location.location_code,
            'name': location.location_name,
            'display_name': location.display_name,
            'gst_number': location.effective_gst,
            'gst_state': location.effective_gst_state,
            'address': location.full_address,
            'is_head_office': location.is_head_office,
        }
        return JsonResponse(data)

    except Location.DoesNotExist:
        return JsonResponse({'error': 'Location not found'}, status=404)


from django.shortcuts import render

# Create your views here.
