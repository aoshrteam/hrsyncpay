# apps/company/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import Company, CompanyUser  # ✅ Both imported
from .forms import CompanyForm, CompanyUserForm


# from apps.core.decorators import admin_required  # ✅ Comment this line


@login_required
def company_list(request):
    """Company List View"""
    companies = Company.objects.all().order_by('name')

    # Search
    search = request.GET.get('search')
    if search:
        companies = companies.filter(name__icontains=search)

    # Pagination
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_companies': companies.count(),
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Companies', 'active': True},
        ],
    }
    return render(request, 'company/company_list.html', context)


@login_required
# @admin_required  # ✅ Comment this line
@transaction.atomic
def company_create(request):
    """Create New Company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()

            # Add current user as Super Admin of this company
            CompanyUser.objects.create(
                company=company,
                user=request.user,
                role='SUPER_ADMIN',
                can_create_employee=True,
                can_edit_employee=True,
                can_delete_employee=True,
                can_create_client=True,
                can_edit_client=True,
                can_delete_client=True,
                can_process_payroll=True,
                can_make_payment=True,
                can_view_reports=True,
                can_manage_settings=True,
            )

            messages.success(request, f'Company {company.name} created successfully!')
            return redirect('company:company_detail', pk=company.pk)
    else:
        form = CompanyForm()

    context = {
        'form': form,
        'title': 'Create Company',
        'button_text': 'Save Company',
    }
    return render(request, 'company/company_form.html', context)


@login_required
def company_detail(request, pk):
    """Company Detail View"""
    company = get_object_or_404(Company, pk=pk)
    users = company.company_users.all()

    context = {
        'company': company,
        'users': users,
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/', 'active': False},
            {'name': 'Companies', 'url': '/company/', 'active': False},
            {'name': company.name, 'active': True},
        ],
    }
    return render(request, 'company/company_detail.html', context)


@login_required
# @admin_required  # ✅ Comment this line
def company_edit(request, pk):
    """Edit Company"""
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f'Company {company.name} updated successfully!')
            return redirect('company:company_detail', pk=company.pk)
    else:
        form = CompanyForm(instance=company)

    context = {
        'form': form,
        'company': company,
        'title': 'Edit Company',
        'button_text': 'Update Company',
    }
    return render(request, 'company/company_form.html', context)


@login_required
# @admin_required  # ✅ Comment this line
def company_delete(request, pk):
    """Delete Company"""
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        name = company.name
        company.delete()
        messages.success(request, f'Company {name} deleted successfully!')
        return redirect('company:company_list')

    context = {
        'company': company,
    }
    return render(request, 'company/company_confirm_delete.html', context)


@login_required
# @admin_required  # ✅ Comment this line
def company_add_user(request, pk):
    """Add User to Company"""
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        form = CompanyUserForm(request.POST)
        if form.is_valid():
            company_user = form.save(commit=False)
            company_user.company = company

            # Set permissions based on role
            role = form.cleaned_data.get('role')
            company_user.can_create_employee = role in ['SUPER_ADMIN', 'ADMIN', 'HR']
            company_user.can_edit_employee = role in ['SUPER_ADMIN', 'ADMIN', 'HR']
            company_user.can_delete_employee = role in ['SUPER_ADMIN', 'ADMIN']
            company_user.can_create_client = role in ['SUPER_ADMIN', 'ADMIN']
            company_user.can_edit_client = role in ['SUPER_ADMIN', 'ADMIN']
            company_user.can_delete_client = role in ['SUPER_ADMIN', 'ADMIN']
            company_user.can_process_payroll = role in ['SUPER_ADMIN', 'ADMIN', 'ACCOUNTANT']
            company_user.can_make_payment = role in ['SUPER_ADMIN', 'ADMIN', 'ACCOUNTANT']
            company_user.can_view_reports = True
            company_user.can_manage_settings = role in ['SUPER_ADMIN', 'ADMIN']

            company_user.save()
            messages.success(request, f'User added to {company.name} successfully!')
            return redirect('company:company_detail', pk=company.pk)
    else:
        form = CompanyUserForm()

    context = {
        'form': form,
        'company': company,
        'title': 'Add User to Company',
        'button_text': 'Add User',
    }
    return render(request, 'company/company_user_form.html', context)


@login_required
# @admin_required  # ✅ Comment this line
def company_remove_user(request, pk):
    """Remove User from Company"""
    company_user = get_object_or_404(CompanyUser, pk=pk)
    company_id = company_user.company.id

    if request.method == 'POST':
        company_user.delete()
        messages.success(request, 'User removed from company successfully!')
        return redirect('company:company_detail', pk=company_id)

    return redirect('company:company_detail', pk=company_id)