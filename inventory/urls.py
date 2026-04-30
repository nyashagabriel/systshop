from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='inventory/index.html', ), name='login'),
    path('products/', views.product_list, name='product_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/',  auth_views.LogoutView.as_view(next_page='login', ), name='logout')
]
