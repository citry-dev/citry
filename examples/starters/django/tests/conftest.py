import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-django-secret")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()
