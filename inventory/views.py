from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Sale, InStock, Branch, Company
from django.db.models import Sum, F, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import SaleForm, ProductForm, InStockForm, CustomUserCreationForm, CustomUserChangeForm, BranchForm, SystemCompanyCreationForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .decorators import rate_limit

def get_user_branches(user):
    if not hasattr(user, 'profile') or not user.profile.company:
        return Branch.objects.none()
    if user.profile.role == 'ADMIN':
        return user.profile.company.branches.all()
    elif user.profile.branch:
        return Branch.objects.filter(id=user.profile.branch.id)
    return Branch.objects.none()

def get_user_products(user):
    return Product.objects.filter(branch__in=get_user_branches(user))

def get_user_sales(user):
    return Sale.objects.filter(branch__in=get_user_branches(user))

def get_user_personnel(user):
    if not hasattr(user, 'profile') or not user.profile.company:
        return User.objects.none()
    
    base_qs = User.objects.filter(is_superuser=False)
    
    if user.profile.role == 'ADMIN':
        return base_qs.filter(profile__company=user.profile.company)
    elif user.profile.branch:
        return base_qs.filter(profile__branch=user.profile.branch)
    return User.objects.none()

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'

def is_manager(user):
    return hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'MANAGER']

def is_tenant_user(user):
    return hasattr(user, 'profile') and user.profile.company is not None and user.profile.company.status == 'ACTIVE'

admin_required = user_passes_test(is_admin)
manager_required = user_passes_test(is_manager)
tenant_required = user_passes_test(is_tenant_user, login_url='/admin/')
system_admin_required = user_passes_test(lambda u: u.is_superuser, login_url='/')

@manager_required
def user_list(request):
    users = get_user_personnel(request.user).select_related('profile')
    return render(request, 'inventory/user_list.html', {'users': users})

@manager_required
def user_add(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Managers can only create staff
            if not is_admin(request.user) and form.cleaned_data.get('role') != 'STAFF':
                messages.error(request, 'Managers can only create Staff users.')
            else:
                new_user = form.save()
                # Assign to correct company and branch
                new_user.profile.company = request.user.profile.company
                if not is_admin(request.user):
                    new_user.profile.branch = request.user.profile.branch
                new_user.profile.save()
                messages.success(request, 'User added successfully.')
                return redirect('user_list')
    else:
        form = CustomUserCreationForm()
        if not is_admin(request.user):
            form.fields['role'].choices = [('STAFF', 'Staff (Till Operator)')]
            # Branch assignment is automatic for branch-scoped managers
            pass
            
    return render(request, 'inventory/user_form.html', {'form': form, 'title': 'Add Personnel'})

@manager_required
def user_edit(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk, profile__company=request.user.profile.company)
    
    if user_to_edit.is_superuser:
        messages.error(request, 'System Administrators cannot be edited here.')
        return redirect('user_list')
    
    # Managers cannot edit Admins or other Managers
    if not is_admin(request.user) and hasattr(user_to_edit, 'profile') and user_to_edit.profile.role != 'STAFF':
        messages.error(request, 'You do not have permission to edit this user.')
        return redirect('user_list')
        
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            if not is_admin(request.user) and form.cleaned_data.get('role') != 'STAFF':
                messages.error(request, 'Managers can only assign the Staff role.')
            else:
                form.save()
                messages.success(request, 'User updated.')
                return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user_to_edit)
        if not is_admin(request.user):
            form.fields['role'].choices = [('STAFF', 'Staff (Till Operator)')]
            
    return render(request, 'inventory/user_form.html', {'form': form, 'title': 'Edit Personnel'})


@admin_required
def branch_list(request):
    branches = request.user.profile.company.branches.all()
    return render(request, 'inventory/branch_list.html', {'branches': branches})

@admin_required
def add_branch(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.company = request.user.profile.company
            branch.save()
            messages.success(request, 'Branch created successfully.')
            return redirect('branch_list')
    else:
        form = BranchForm()
    return render(request, 'inventory/branch_form.html', {'form': form, 'title': 'Create Branch'})

@admin_required
def user_delete(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk, profile__company=request.user.profile.company)
    if user_to_delete.is_superuser:
        messages.error(request, 'System Administrators cannot be deleted.')
        return redirect('user_list')
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete yourself.')
    elif user_to_delete.profile.role == 'ADMIN' and User.objects.filter(profile__company=request.user.profile.company, profile__role='ADMIN').count() <= 1:
        messages.error(request, 'You cannot delete the last Administrator of the company.')
    else:
        user_to_delete.delete()
        messages.success(request, 'Personnel deleted successfully.')
    return redirect('user_list')

@tenant_required                                    # FIX B5 & B6
def dashboard(request):
    products = get_user_products(request.user)
    sales = get_user_sales(request.user)
    
    total_products   = products.count()
    total_stock_value = products.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0
    low_stock_items  = products.filter(quantity__lte=F('low_stock_threshold'))
    recent_sales     = sales.select_related('product', 'sold_by').order_by('-timestamp')[:10]
    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
    }
    return render(request, 'inventory/dashboard.html', context)


@tenant_required                                    # FIX B5
def product_list(request):
    products = get_user_products(request.user)
    return render(request, 'inventory/product_list.html', {'products': products})


@manager_required
@rate_limit(requests=60, window=60) # Protect against scripting mass fake products
def add_product(request):                         # NEW: was missing entirely
    if request.method == 'POST':
        form = ProductForm(request.POST)
        # Limit branch choices to user's allowed branches
        branches = get_user_branches(request.user)
        form.fields['branch'].queryset = branches
        if form.is_valid():
            product = form.save(commit=False)
            if not product.branch:
                if not is_admin(request.user):
                    product.branch = request.user.profile.branch
                elif branches.count() == 1:
                    product.branch = branches.first()
            
            if not product.branch:
                messages.error(request, 'Please select a branch.')
                return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})
                
            product.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()
        form.fields['branch'].queryset = get_user_branches(request.user)
        if not is_admin(request.user):
            form.fields['branch'].initial = request.user.profile.branch
            from django import forms
            form.fields['branch'].widget = forms.HiddenInput()
            form.fields['branch'].required = False # It will be set in save(commit=False)
        elif form.fields['branch'].queryset.count() == 1:
            form.fields['branch'].initial = form.fields['branch'].queryset.first()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


@manager_required
def edit_product(request, pk):                   # NEW: was missing entirely
    product = get_object_or_404(get_user_products(request.user), pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        form.fields['branch'].queryset = get_user_branches(request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
        form.fields['branch'].queryset = get_user_branches(request.user)
        if not is_admin(request.user):
            from django import forms
            form.fields['branch'].widget = forms.HiddenInput()
        elif form.fields['branch'].queryset.count() == 1:
            form.fields['branch'].initial = form.fields['branch'].queryset.first()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Edit Product'})


@tenant_required
@rate_limit(requests=120, window=60) # Allow 2 sales per second max per IP
def record_sale_view(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        form.fields['product'].queryset = get_user_products(request.user)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.sold_by = request.user
            sale.branch = sale.product.branch
            product = sale.product
            if product.quantity >= sale.quantity_sold:
                sale.save()
                messages.success(request, f'Sale recorded: {sale.quantity_sold}x {product.name}.')
                return redirect('dashboard')
            else:
                messages.error(request, f'Insufficient stock. Only {product.quantity} remaining.')
    else:
        form = SaleForm()
        form.fields['product'].queryset = get_user_products(request.user)
    return render(request, 'inventory/record_sale.html', {'form': form, 'title': 'Record a Sale'})


@tenant_required
def stock_in_view(request):                       # NEW: was missing entirely
    if request.method == 'POST':
        form = InStockForm(request.POST)
        form.fields['product'].queryset = get_user_products(request.user)
        if form.is_valid():
            stock_entry = form.save(commit=False)
            stock_entry.added_by = request.user
            stock_entry.branch = stock_entry.product.branch
            stock_entry.save()
            messages.success(request, f'Stock updated: +{stock_entry.quantity_added} {stock_entry.product.name}.')
            return redirect('product_list')
    else:
        form = InStockForm()
        form.fields['product'].queryset = get_user_products(request.user)
    return render(request, 'inventory/stock_in.html', {'form': form, 'title': 'Stock In'})


@tenant_required
def sales_history(request):                       # NEW: was missing entirely
    sales = get_user_sales(request.user).select_related('product', 'sold_by').order_by('-timestamp')
    return render(request, 'inventory/sales_history.html', {'sales': sales})

# --- SYSTEM ADMIN VIEWS ---

@system_admin_required
def system_dashboard(request):
    total_companies = Company.objects.count()
    active_companies = Company.objects.filter(status='ACTIVE').count()
    total_users = User.objects.count()
    total_branches = Branch.objects.count()
    
    context = {
        'total_companies': total_companies,
        'active_companies': active_companies,
        'total_users': total_users,
        'total_branches': total_branches,
    }
    return render(request, 'inventory/system_dashboard.html', context)

@system_admin_required
def system_company_list(request):
    companies = Company.objects.annotate(
        user_count=Count('users'),
        branch_count=Count('branches')
    ).order_by('-created_at')
    return render(request, 'inventory/system_company_list.html', {'companies': companies})

@system_admin_required
def system_company_add(request):
    if request.method == 'POST':
        form = SystemCompanyCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company and Admin created successfully.')
            return redirect('system_company_list')
    else:
        form = SystemCompanyCreationForm()
    return render(request, 'inventory/system_company_form.html', {'form': form, 'title': 'Add New Company'})

@system_admin_required
def system_company_status(request, pk):
    company = get_object_or_404(Company, pk=pk)
    
    if company.status == 'ACTIVE':
        company.status = 'PENDING_DELETION'
        messages.warning(request, f'{company.name} is now pending deletion (2 month warning).')
    elif company.status == 'PENDING_DELETION':
        company.status = 'PAUSED'
        messages.warning(request, f'{company.name} is now paused (1 month final warning).')
    elif company.status == 'PAUSED':
        name = company.name
        company.delete()
        messages.success(request, f'Company {name} has been permanently deleted.')
        return redirect('system_company_list')
    
    company.status_updated_at = timezone.now()
    company.save()
    return redirect('system_company_list')