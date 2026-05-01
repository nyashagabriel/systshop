from django.shortcuts import render, redirect
from .models import Product, Sale
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from .forms import SaleForm
from django.contrib import messages
# Create your views here.


def index(request):
    return render(request, 'index.html')

def product_list(request):
    
    all_products = Product.objects.all()
    context = {'products': all_products}
    return render(request, 'inventory/product_list.html', context)

@login_required(login_url='')
def dashboard(request):
    #get all products total
    total_products = Product.objects.count()
    
    #search stock value
    stock_value_query = Product.objects.aggregate(total=Sum(F('price') * F('quantity')))
    
    #getting actual value
    total_stock_value = stock_value_query['total'] or 0
    
    #low stock
    low_stock_items = Product.objects.filter(quantity__lte=F('low_stock_threshold'))
    
    #recent sales
    recent_sales = Sale.objects.all().order_by('-timestamp')[:10]
    
    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales
    }
    
    return render(request, 'inventory/dashboard.html', context)



@login_required(login_url='/login/')
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
                return redirect('product_list')
            else:
                messages.error(request, f'Insufficient stock! Only {product.quantity} units remaining.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SaleForm()

    context = {
        'form': form,
        'title': 'Record a Sale'
    }
    return render(request, 'inventory/record_sale.html', context)