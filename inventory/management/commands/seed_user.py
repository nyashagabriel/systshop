from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a test user for local development and Render deployment'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Username (default: admin)')
        parser.add_argument('--password', default='admin123', help='Password (default: admin123)')
        parser.add_argument('--email', default='admin@test.com', help='Email (default: admin@test.com)')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
            return

        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f'✓ User {username} created successfully'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
