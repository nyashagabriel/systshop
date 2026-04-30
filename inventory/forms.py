from django import forms
from .models import Product
class LogIn(forms.Form):
    username = forms.CharField(max_length=200)
    password = forms.PasswordInput()
    
    def LogIn(self):
        print("LoggedIn")
        
class ProductForm(forms.ModelForm):
    class Meta():
        model = Product
        fields = ['name', 'category', 'price', 'quantity']