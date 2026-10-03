"""
Create or update the admin accounts configured through environment variables.

  DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD
      Full-access superuser. The password is reset to the configured value on every run.
  DEMO_VIEWER_USERNAME / DEMO_VIEWER_PASSWORD
      Staff user in the "Demo viewers" group with only view permissions on admin_app models,
      safe to share publicly (e.g. on a portfolio).
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

DEMO_GROUP = 'Demo viewers'


class Command(BaseCommand):
    help = 'Ensure the superuser and optional view-only demo user from environment variables exist.'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if username and password:
            user, created = User.objects.get_or_create(username=username)
            user.email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
            self.stdout.write(f"[admin] Superuser '{username}' {'created' if created else 'updated'}")

        viewer = os.environ.get('DEMO_VIEWER_USERNAME', '').strip()
        viewer_password = os.environ.get('DEMO_VIEWER_PASSWORD', '')
        if viewer and viewer_password:
            group, _ = Group.objects.get_or_create(name=DEMO_GROUP)
            group.permissions.set(
                Permission.objects.filter(content_type__app_label='admin_app', codename__startswith='view_')
            )
            user, created = User.objects.get_or_create(username=viewer)
            user.is_staff = True
            user.is_superuser = False
            user.is_active = True
            user.set_password(viewer_password)
            user.save()
            user.groups.set([group])
            self.stdout.write(
                f"[admin] View-only user '{viewer}' {'created' if created else 'updated'} "
                f"({group.permissions.count()} view permissions)"
            )
