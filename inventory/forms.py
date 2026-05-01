from django import forms
from .models import Product, Sale
        
class ProductForm(forms.ModelForm):
    class Meta():
        model = Product
        fields = ['name', 'category', 'price', 'quantity']
        
        
class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'quantity_sold']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only list products that have remaining stock
        self.fields['product'].queryset = Product.objects.filter(quantity__gt=0)
        self.fields['quantity_sold'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter quantity'
        })