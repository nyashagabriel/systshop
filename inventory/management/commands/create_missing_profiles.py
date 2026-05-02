from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile

class Command(BaseCommand):
    help = 'Creates UserProfiles for any existing users that do not have one.'

    def handle(self, *args, **options):
        users_without_profile = 0
        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                role = 'ADMIN' if user.is_superuser else 'STAFF'
                UserProfile.objects.create(user=user, role=role)
                self.stdout.write(self.style.SUCCESS(f'Created profile for: {user.username} (Role: {role})'))
                users_without_profile += 1
        
        if users_without_profile == 0:
            self.stdout.write(self.style.SUCCESS('All users already have profiles. Nothing to do!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully created {users_without_profile} missing profiles.'))
