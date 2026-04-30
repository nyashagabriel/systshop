from django.shortcuts import render
from .models import Product, Sale
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
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
