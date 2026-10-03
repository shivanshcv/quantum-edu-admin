"""
R2 upload service for Cloudflare R2 (S3-compatible).
"""
import logging
import uuid
from django.conf import settings

logger = logging.getLogger(__name__)


def get_r2_client():
    """Return boto3 S3 client configured for R2."""
    import boto3
    from botocore.config import Config

    return boto3.client(
        's3',
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )


def upload_file_to_r2(file_obj, object_key: str, content_type: str = None) -> str:
    """
    Upload a file to R2 and return the public URL.
    :param file_obj: File-like object (e.g. from request.FILES)
    :param object_key: S3 object key (e.g. products/1/thumbnail.jpg)
    :param content_type: Optional MIME type
    :return: Public URL (e.g. https://pub-xxx.r2.dev/products/1/thumbnail.jpg)
    """
    if not settings.R2_ENABLED:
        logger.warning("R2 upload skipped: R2_ENABLED is False")
        raise ValueError("R2 is not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY.")

    logger.info("[R2] upload_file_to_r2 starting: bucket=%s key=%s content_type=%s", settings.R2_BUCKET_NAME, object_key, content_type)
    try:
        client = get_r2_client()
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        client.upload_fileobj(file_obj, settings.R2_BUCKET_NAME, object_key, ExtraArgs=extra_args or None)
        base = settings.R2_PUBLIC_URL.rstrip('/')
        url = f"{base}/{object_key}"
        logger.info("[R2] upload_file_to_r2 SUCCESS: url=%s", url)
        return url
    except Exception as e:
        logger.exception("[R2] upload_file_to_r2 FAILED: bucket=%s key=%s error=%s", settings.R2_BUCKET_NAME, object_key, e)
        raise


def build_object_key(prefix: str, entity_id: int, filename: str, suffix: str = None) -> str:
    """
    Build object key for R2.
    :param prefix: e.g. 'products' or 'lessons'
    :param entity_id: Product or Lesson ID
    :param filename: Original filename
    :param suffix: Optional suffix (e.g. 'thumbnail', 'preview') to avoid collisions
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    if suffix:
        return f"{prefix}/{entity_id}/{suffix}.{ext}"
    unique = uuid.uuid4().hex[:8]
    return f"{prefix}/{entity_id}/{unique}.{ext}"
