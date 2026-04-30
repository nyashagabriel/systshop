from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    price = models.DecimalField(decimal_places=3, max_digits=1000)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.IntegerField(default=0)
    sold_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.product.quantity >= self.quantity_sold:
            self.product.quantity -= self.quantity_sold
            self.product.save()
            super().save(**args, **kwargs)
        else:
            ValidationError(f"There is not enough to make a sale for {self.product.name}")
        
    

class InStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_added = models.IntegerField(default=0)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
