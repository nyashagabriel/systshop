from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .decorators import rate_limit

urlpatterns = [
    # Limit login attempts to 5 per minute per IP
    path('', rate_limit(requests=5, window=60)(auth_views.LoginView.as_view(template_name='inventory/index.html')), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('personnel/', views.user_list, name='user_list'),
    path('personnel/add/', views.user_add, name='user_add'),
    path('personnel/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('personnel/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.add_branch, name='add_branch'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),

    path('sales/record/', views.record_sale_view, name='record_sale'),
    path('sales/history/', views.sales_history, name='sales_history'),

    path('stock/in/', views.stock_in_view, name='stock_in'),

    # --- SYSTEM ADMIN URLS ---
    path('system/', views.system_dashboard, name='system_dashboard'),
    path('system/companies/', views.system_company_list, name='system_company_list'),
    path('system/companies/add/', views.system_company_add, name='system_company_add'),
    path('system/companies/<int:pk>/status/', views.system_company_status, name='system_company_status'),
]