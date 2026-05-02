from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import Company, Branch, Product, Sale, InStock, UserProfile

class Command(BaseCommand):
    help = 'Migrates all existing data to a specified Company and Branch'

    def add_arguments(self, parser):
        parser.add_argument('company_name', type=str, help='The name of the company to migrate to')
        parser.add_argument('branch_name', type=str, help='The name of the branch to migrate to')

    def handle(self, *args, **options):
        company_name = options['company_name']
        branch_name = options['branch_name']

        # 1. Get or create the target Company
        company, created = Company.objects.get_or_create(name=company_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new Company: {company_name}'))

        # 2. Get or create the target Branch
        branch, created = Branch.objects.get_or_create(name=branch_name, company=company)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new Branch: {branch_name} in {company_name}'))

        # 3. Migrate Users
        profiles = UserProfile.objects.all()
        for profile in profiles:
            profile.company = company
            if profile.role != 'ADMIN':
                profile.branch = branch
            profile.save()
        self.stdout.write(self.style.SUCCESS(f'Migrated {profiles.count()} user profiles.'))

        # 4. Migrate Products
        products = Product.objects.all()
        products.update(branch=branch)
        self.stdout.write(self.style.SUCCESS(f'Migrated {products.count()} products.'))

        # 5. Migrate Sales & Stock Ins
        sales = Sale.objects.all()
        sales.update(branch=branch)
        
        stock_ins = InStock.objects.all()
        stock_ins.update(branch=branch)
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {sales.count()} sales and {stock_ins.count()} stock entries.'))
        self.stdout.write(self.style.SUCCESS('Successfully migrated all data to the new multi-tenant structure.'))
