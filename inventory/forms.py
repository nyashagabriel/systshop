from django import forms
from .models import Product, Sale, InStock, UserProfile, Branch, Company
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (Optional)'}),
        }

class SystemCompanyCreationForm(forms.Form):
    company_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    admin_username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admin Username'}))
    admin_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Admin Email'}))
    admin_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Admin Password'}))

    def clean_admin_username(self):
        username = self.cleaned_data['admin_username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username is already taken.')
        return username

    def save(self):
        with transaction.atomic():
            company = Company.objects.create(name=self.cleaned_data['company_name'])
            user = User.objects.create_user(
                username=self.cleaned_data['admin_username'],
                email=self.cleaned_data['admin_email'],
                password=self.cleaned_data['admin_password']
            )
            # The signal will create a profile, we update it
            user.profile.company = company
            user.profile.role = 'ADMIN'
            user.profile.save()
            return company

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # The signal creates the profile, we just need to update its role
            user.profile.role = self.cleaned_data.get('role')
            user.profile.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['role'].initial = self.instance.profile.role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.profile.role = self.cleaned_data.get('role')
            user.profile.save()
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['branch', 'name', 'category', 'price', 'quantity', 'low_stock_threshold']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Snacks, Drinks'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'branch' in self.fields:
            self.fields['branch'].required = False

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'quantity_sold']
        widgets = {
            'quantity_sold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': '1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(quantity__gt=0)
        self.fields['product'].widget.attrs['class'] = 'form-control'


class InStockForm(forms.ModelForm):
    class Meta:
        model = InStock
        fields = ['product', 'quantity_added']
        widgets = {
            'quantity_added': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity to add',
                'min': '1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].widget.attrs['class'] = 'form-control'