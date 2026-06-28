# apps/clients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Client
from .forms import ClientForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from .models import Client
from apps.core.decorators import data_entry_or_admin_required


# apps/clients/views.py

@login_required
def client_list(request):
    """Client List View"""
    clients = Client.objects.all().order_by('name')

    search = request.GET.get('search')
    if search:
        clients = clients.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(contact_person__icontains=search)
        )

    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # ✅ यह सही है - इसमें client.id होगा
        'search': search,
        'total_clients': clients.count(),
    }
    return render(request, 'clients/client_list.html', context)

@login_required
# @data_entry_or_admin_required  # Commented for now
def client_create(request):
    """Create New Client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client {client.name} created successfully!')
            return redirect('clients:client_list')
    else:
        form = ClientForm()

    context = {
        'form': form,
        'title': 'Create Client',
        'button_text': 'Save Client',
    }
    return render(request, 'clients/client_form.html', context)


# apps/clients/views.py

# apps/clients/views.py

@login_required
def client_detail(request, pk):
    """Client Detail View with Assignments Count"""
    client = get_object_or_404(Client, pk=pk)

    # ✅ Get all assignments for this client
    assignments = client.assignments.filter(is_current=True)

    # ✅ Get location-wise employee count
    locations = client.client_locations.filter(is_active=True)
    for location in locations:
        location.employee_count = location.assignments.filter(
            is_current=True,
            employee__is_active=True
        ).values('employee').distinct().count()

    # ✅ Prepare assignment data with employee code
    assignment_data = []
    for assignment in assignments:
        assignment_data.append({
            'id': assignment.id,
            'employee': assignment.employee,
            'employee_code': assignment.employee.employee_code,  # ✅ Add employee_code
            'master_code': assignment.employee.master_code,  # Keep if needed
            'employee_name': assignment.employee.name,
            'location': assignment.location,
            'start_date': assignment.start_date,
            'status': assignment.status,
            'is_current': assignment.is_current,
        })

    context = {
        'client': client,
        'assignments': assignments,
        'assignment_data': assignment_data,  # ✅ Pass to template
        'locations': locations,
        'total_employees': assignments.values('employee').distinct().count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Clients', 'url': '/clients/', 'active': False},
            {'name': client.name, 'active': True},
        ],
    }
    return render(request, 'clients/client_detail.html', context)

@login_required
# @data_entry_or_admin_required  # Commented for now
def client_edit(request, pk):
    """Edit Client"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client {client.name} updated successfully!')
            return redirect('clients:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)

    context = {
        'form': form,
        'client': client,
        'title': 'Edit Client',
        'button_text': 'Update Client',
    }
    return render(request, 'clients/client_form.html', context)


@login_required
# @data_entry_or_admin_required  # Commented for now
def client_delete(request, pk):
    """Delete Client"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        name = client.name
        client.delete()
        messages.success(request, f'Client {name} deleted successfully!')
        return redirect('clients:client_list')

    context = {
        'client': client,
    }
    return render(request, 'clients/client_confirm_delete.html', context)


# apps/clients/views.py - Add these views






