from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Sale, InStock
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from .forms import SaleForm, ProductForm, InStockForm
from django.contrib import messages


@login_required                                    # FIX B5 & B6
def dashboard(request):
    total_products   = Product.objects.count()
    total_stock_value = Product.objects.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0
    low_stock_items  = Product.objects.filter(quantity__lte=F('low_stock_threshold'))
    recent_sales     = Sale.objects.select_related('product', 'sold_by').order_by('-timestamp')[:10]
    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required                                    # FIX B5
def product_list(request):
    products = Product.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products})


@login_required
def add_product(request):                         # NEW: was missing entirely
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
def edit_product(request, pk):                   # NEW: was missing entirely
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Edit Product'})


@login_required
def record_sale_view(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.sold_by = request.user
            product = sale.product
            if product.quantity >= sale.quantity_sold:
                sale.save()
                messages.success(request, f'Sale recorded: {sale.quantity_sold}x {product.name}.')
                return redirect('dashboard')
            else:
                messages.error(request, f'Insufficient stock. Only {product.quantity} remaining.')
    else:
        form = SaleForm()
    return render(request, 'inventory/record_sale.html', {'form': form, 'title': 'Record a Sale'})


@login_required
def stock_in_view(request):                       # NEW: was missing entirely
    if request.method == 'POST':
        form = InStockForm(request.POST)
        if form.is_valid():
            stock_entry = form.save(commit=False)
            stock_entry.added_by = request.user
            stock_entry.save()
            messages.success(request, f'Stock updated: +{stock_entry.quantity_added} {stock_entry.product.name}.')
            return redirect('product_list')
    else:
        form = InStockForm()
    return render(request, 'inventory/stock_in.html', {'form': form, 'title': 'Stock In'})


@login_required
def sales_history(request):                       # NEW: was missing entirely
    sales = Sale.objects.select_related('product', 'sold_by').order_by('-timestamp')
    return render(request, 'inventory/sales_history.html', {'sales': sales})