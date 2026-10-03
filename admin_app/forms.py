"""
Admin forms with R2 file upload support.
"""
import logging

from django import forms
from django.core.exceptions import ValidationError

from .models import Lesson, Product, ProductContent

logger = logging.getLogger(__name__)

# quantum-edu-be JPA @Enumerated(EnumType.STRING) names (must match exactly)
DIFFICULTY_LEVEL_CHOICES = [
    ('BEGINNER', 'BEGINNER'),
    ('INTERMEDIATE', 'INTERMEDIATE'),
    ('ADVANCED', 'ADVANCED'),
]
PRODUCT_CONTENT_TYPE_CHOICES = [
    ('LESSON', 'LESSON'),
    ('ASSESSMENT', 'ASSESSMENT'),
]
LESSON_TYPE_CHOICES = [
    ('VIDEO', 'VIDEO'),
    ('PDF', 'PDF'),
    ('PPT', 'PPT'),
]


class ProductAdminForm(forms.ModelForm):
    """Product form with thumbnail and preview video upload to R2."""
    upload_thumbnail = forms.FileField(required=False, label='Upload thumbnail (replaces URL)')
    upload_preview_video = forms.FileField(required=False, label='Upload preview video (replaces URL)')
    difficulty_level = forms.ChoiceField(
        choices=[('', '---------')] + DIFFICULTY_LEVEL_CHOICES,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        files = kwargs.get('files') or {}
        if files:
            logger.info("[R2] ProductAdminForm.__init__: request.FILES keys=%s", list(files.keys()))
        if (
            not self.is_bound
            and getattr(self.instance, 'pk', None)
            and getattr(self.instance, 'difficulty_level', None) in (None, '')
        ):
            self.initial['difficulty_level'] = ''

    class Meta:
        model = Product
        fields = '__all__'

    ALLOWED_IMAGE = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
    ALLOWED_VIDEO = ('video/mp4', 'video/webm')
    MAX_IMAGE_MB = 5
    MAX_VIDEO_MB = 100

    def clean_upload_thumbnail(self):
        f = self.files.get('upload_thumbnail') if hasattr(self, 'files') and self.files else None
        logger.info("[R2] Product clean_upload_thumbnail: files_keys=%s has_upload_thumbnail=%s",
                    list(self.files.keys()) if hasattr(self, 'files') and self.files else [], bool(f))
        if not f:
            return None
        if f.content_type not in self.ALLOWED_IMAGE:
            logger.warning("[R2] Product upload_thumbnail rejected: content_type=%s", f.content_type)
            raise ValidationError('Allowed: JPEG, PNG, WebP, GIF')
        if f.size > self.MAX_IMAGE_MB * 1024 * 1024:
            logger.warning("[R2] Product upload_thumbnail rejected: size=%s", f.size)
            raise ValidationError(f'Max size: {self.MAX_IMAGE_MB} MB')
        logger.info("[R2] Product upload_thumbnail validated: name=%s size=%s type=%s", f.name, f.size, f.content_type)
        return f

    def clean_upload_preview_video(self):
        f = self.files.get('upload_preview_video') if hasattr(self, 'files') and self.files else None
        logger.info("[R2] Product clean_upload_preview_video: files_keys=%s has_upload_preview_video=%s",
                    list(self.files.keys()) if hasattr(self, 'files') and self.files else [], bool(f))
        if not f:
            return None
        if f.content_type not in self.ALLOWED_VIDEO:
            logger.warning("[R2] Product upload_preview_video rejected: content_type=%s", f.content_type)
            raise ValidationError('Allowed: MP4, WebM')
        if f.size > self.MAX_VIDEO_MB * 1024 * 1024:
            logger.warning("[R2] Product upload_preview_video rejected: size=%s", f.size)
            raise ValidationError(f'Max size: {self.MAX_VIDEO_MB} MB')
        logger.info("[R2] Product upload_preview_video validated: name=%s size=%s type=%s", f.name, f.size, f.content_type)
        return f

    def clean_difficulty_level(self):
        value = self.cleaned_data.get('difficulty_level')
        return value if value else None

    def save(self, commit=True):
        return super().save(commit=commit)


class ProductContentAdminForm(forms.ModelForm):
    """Restrict content_type to catalogue ContentType enum values."""
    content_type = forms.ChoiceField(choices=PRODUCT_CONTENT_TYPE_CHOICES, required=True)

    class Meta:
        model = ProductContent
        fields = '__all__'


class LessonAdminForm(forms.ModelForm):
    """Lesson form with video, PDF, PPT upload to R2."""
    lesson_type = forms.ChoiceField(choices=LESSON_TYPE_CHOICES, required=True)
    upload_video = forms.FileField(required=False, label='Upload video (replaces URL)')
    upload_pdf = forms.FileField(required=False, label='Upload PDF (replaces URL)')
    upload_ppt = forms.FileField(required=False, label='Upload PPT (replaces URL)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        files = kwargs.get('files') or {}
        if files:
            logger.info("[R2] LessonAdminForm.__init__: request.FILES keys=%s", list(files.keys()))

    class Meta:
        model = Lesson
        fields = '__all__'

    ALLOWED_VIDEO = ('video/mp4', 'video/webm')
    ALLOWED_PDF = ('application/pdf',)
    ALLOWED_PPT = (
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    )
    MAX_VIDEO_MB = 500
    MAX_PDF_MB = 50
    MAX_PPT_MB = 50

    def clean_upload_video(self):
        # Use add_prefix for formset compatibility (inline forms have prefixed keys e.g. lesson-0-upload_video)
        key = self.add_prefix('upload_video')
        f = self.files.get(key) if hasattr(self, 'files') and self.files else None
        logger.info("[R2] Lesson clean_upload_video: key=%s files_keys=%s has_file=%s", key, list(self.files.keys()) if hasattr(self, 'files') and self.files else [], bool(f))
        if not f:
            return None
        if f.content_type not in self.ALLOWED_VIDEO:
            raise ValidationError('Allowed: MP4, WebM')
        if f.size > self.MAX_VIDEO_MB * 1024 * 1024:
            raise ValidationError(f'Max size: {self.MAX_VIDEO_MB} MB')
        logger.info("[R2] Lesson upload_video validated: name=%s size=%s", f.name, f.size)
        return f

    def clean_upload_pdf(self):
        # Use add_prefix for formset compatibility (inline forms have prefixed keys)
        key = self.add_prefix('upload_pdf')
        f = self.files.get(key) if hasattr(self, 'files') and self.files else None
        logger.info("[R2] Lesson clean_upload_pdf: key=%s files_keys=%s has_file=%s", key, list(self.files.keys()) if hasattr(self, 'files') and self.files else [], bool(f))
        if not f:
            return None
        if f.content_type not in self.ALLOWED_PDF:
            raise ValidationError('Allowed: PDF')
        if f.size > self.MAX_PDF_MB * 1024 * 1024:
            raise ValidationError(f'Max size: {self.MAX_PDF_MB} MB')
        logger.info("[R2] Lesson upload_pdf validated: name=%s size=%s", f.name, f.size)
        return f

    def clean_upload_ppt(self):
        # Use add_prefix for formset compatibility (inline forms have prefixed keys)
        key = self.add_prefix('upload_ppt')
        f = self.files.get(key) if hasattr(self, 'files') and self.files else None
        logger.info("[R2] Lesson clean_upload_ppt: key=%s files_keys=%s has_file=%s", key, list(self.files.keys()) if hasattr(self, 'files') and self.files else [], bool(f))
        if not f:
            return None
        if f.content_type not in self.ALLOWED_PPT:
            raise ValidationError('Allowed: PPT, PPTX')
        if f.size > self.MAX_PPT_MB * 1024 * 1024:
            raise ValidationError(f'Max size: {self.MAX_PPT_MB} MB')
        logger.info("[R2] Lesson upload_ppt validated: name=%s size=%s", f.name, f.size)
        return f

    def save(self, commit=True):
        return super().save(commit=commit)
