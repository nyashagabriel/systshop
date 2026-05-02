from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class Company(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING_DELETION', 'Pending Deletion'),
        ('PAUSED', 'Paused'),
    )
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    status_updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Company Administrator'),
        ('MANAGER', 'Branch Manager'),
        ('STAFF', 'Staff (Till Operator)'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='users')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'STAFF'
        UserProfile.objects.create(user=instance, role=role)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Product(models.Model):
    branch             = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name='products')
    name               = models.CharField(max_length=200)
    category           = models.CharField(max_length=200)
    price              = models.DecimalField(max_digits=10, decimal_places=2)  # FIX B3
    quantity           = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)

    def __str__(self):                             # FIX B4
        return f"{self.name} ({self.category})"

    @property
    def stock_value(self):
        return self.price * self.quantity

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    class Meta:
        ordering = ['name']


class Sale(models.Model):
    branch        = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name='sales')
    product       = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.IntegerField(default=0)
    sold_by       = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.product.quantity < self.quantity_sold:
            raise ValidationError(                    # FIX B1: raise, not just call
                f"Not enough stock for {self.product.name}. "
                f"Available: {self.product.quantity}"
            )
        self.product.quantity -= self.quantity_sold
        self.product.save()
        super().save(*args, **kwargs)               # FIX B1: *args not **args

    def __str__(self):                             # FIX B4
        return f"{self.quantity_sold}x {self.product.name} by {self.sold_by}"

    class Meta:
        ordering = ['-timestamp']


class InStock(models.Model):
    branch         = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name='stock_ins')
    product        = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_added = models.IntegerField(default=0)
    added_by       = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp      = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):               # FIX B2: was completely missing
        if self.quantity_added <= 0:
            raise ValidationError("Quantity added must be greater than zero.")
        self.product.quantity += self.quantity_added
        self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):                             # FIX B4
        return f"+{self.quantity_added} {self.product.name} by {self.added_by}"

    class Meta:
        ordering = ['-timestamp']