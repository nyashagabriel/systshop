"""
WSGI config for sys_shop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sys_shop.settings')

# Create application
application = get_wsgi_application()

# Auto-create a superuser when environment variables are provided.
# This is idempotent: it checks for existing user before creating.
try:
	from django.conf import settings
	if os.environ.get('CREATE_SUPERUSER', '').lower() in ('1', 'true', 'yes'):
		from django.contrib.auth import get_user_model
		User = get_user_model()
		username = os.environ.get('SUPERUSER_USERNAME', 'admin')
		email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
		password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')
		if not User.objects.filter(username=username).exists():
			User.objects.create_superuser(username=username, email=email, password=password)
			# Avoid importing logging; simple stdout message is fine here
			print(f"Created superuser '{username}' via WSGI startup")
except Exception:
	# Don't let superuser creation block the app if database isn't ready yet.
	pass
