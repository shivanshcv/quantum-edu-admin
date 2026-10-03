"""
Management command to verify R2 configuration.
Usage: python manage.py check_r2
"""
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify Cloudflare R2 configuration for media uploads'

    def handle(self, *args, **options):
        r2_enabled = getattr(settings, 'R2_ENABLED', False)
        self.stdout.write(f"R2_ENABLED: {r2_enabled}")

        if not r2_enabled:
            self.stdout.write(self.style.WARNING(
                "R2 is NOT enabled. Upload fields will be hidden and files will not be stored to R2.\n"
                "Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in deploy.env and redeploy."
            ))
            return

        acc = getattr(settings, 'R2_ACCOUNT_ID', '')
        key = getattr(settings, 'R2_ACCESS_KEY_ID', '')
        secret = getattr(settings, 'R2_SECRET_ACCESS_KEY', '')
        self.stdout.write(f"R2_ACCOUNT_ID: {acc[:8]}... (len={len(acc)})")
        self.stdout.write(f"R2_ACCESS_KEY_ID: len={len(key)} (must be 32 for R2 S3 API)")
        self.stdout.write(f"R2_SECRET_ACCESS_KEY: len={len(secret)} (must be 64)")
        self.stdout.write(f"R2_BUCKET_NAME: {getattr(settings, 'R2_BUCKET_NAME', '')}")
        self.stdout.write(f"R2_PUBLIC_URL: {getattr(settings, 'R2_PUBLIC_URL', '')}")
        if len(key) != 32:
            self.stdout.write(self.style.WARNING(
                f"R2_ACCESS_KEY_ID has length {len(key)}, should be 32. "
                "Use R2 API token from Manage R2 API Tokens (NOT cf_/cfut_ Cloudflare API tokens)."
            ))

        # Try a test connection
        try:
            from admin_app.services import get_r2_client
            client = get_r2_client()
            try:
                client.head_bucket(Bucket=settings.R2_BUCKET_NAME)
                self.stdout.write(self.style.SUCCESS("R2 bucket accessible. Uploads should work."))
            except Exception as head_err:
                # HeadBucket can fail; try list_objects to verify bucket exists
                client.list_objects_v2(Bucket=settings.R2_BUCKET_NAME, MaxKeys=1)
                self.stdout.write(self.style.SUCCESS("R2 bucket reachable (list works). Uploads should work."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"R2 connection failed: {e}"))
            self.stdout.write(
                "Check: 1) Bucket 'quantum-edu-media' exists in Cloudflare R2. "
                "2) API token has Object Read & Write. 3) R2_PUBLIC_URL matches your bucket's public URL."
            )
