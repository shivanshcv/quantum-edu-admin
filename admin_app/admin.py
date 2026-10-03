"""
Django admin registration for all quantum_education tables.
"""
import logging

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .assessment_csv import replace_assessment_questions_from_csv_file
from .services import upload_file_to_r2, build_object_key

logger = logging.getLogger(__name__)

from .forms import LessonAdminForm, ProductAdminForm, ProductContentAdminForm
from .models import (
    AuthUser,
    UserProfile,
    Category,
    Product,
    ProductCategory,
    ProductModule,
    ProductContent,
    Lesson,
    Assessment,
    AssessmentQuestion,
    AssessmentOption,
    CartItem,
    Order,
    CourseOwnership,
    UserLessonProgress,
    UserAssessmentResult,
)


@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified')
    search_fields = ('email',)
    readonly_fields = ('created_at', 'updated_at', 'last_login_at')
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'city', 'created_at')
    list_filter = ('country',)
    search_fields = ('first_name', 'last_name', 'billing_name', 'phone')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'parent', 'level', 'is_active', 'created_at')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'slug')
    raw_id_fields = ('parent',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('level', 'name')


class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    raw_id_fields = ('category',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'id', 'title', 'slug', 'price', 'difficulty_level',
        'is_published', 'is_featured', 'is_free', 'created_at'
    )
    list_filter = ('is_published', 'is_featured', 'is_free', 'difficulty_level')
    search_fields = ('title', 'slug', 'short_description')
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview', 'preview_video_link')
    inlines = [ProductCategoryInline]
    ordering = ('-created_at',)

    def get_fieldsets(self, request, obj=None):
        r2_enabled = getattr(settings, 'R2_ENABLED', False)
        logger.info("[R2] ProductAdmin get_fieldsets: R2_ENABLED=%s (upload fields %s)", r2_enabled, "VISIBLE" if r2_enabled else "HIDDEN")
        media_fields = (
            'upload_thumbnail', 'thumbnail_url', 'thumbnail_preview',
            'upload_preview_video', 'preview_video_url', 'preview_video_link',
        ) if r2_enabled else (
            'thumbnail_url', 'thumbnail_preview',
            'preview_video_url', 'preview_video_link',
        )
        return (
            (None, {'fields': ('title', 'slug', 'short_description', 'long_description')}),
            ('Media (upload or paste URL)', {'fields': media_fields}),
            ('Pricing & Meta', {'fields': ('price', 'discount_price', 'difficulty_level', 'duration_minutes')}),
            ('Flags', {'fields': ('is_published', 'is_featured', 'is_free')}),
            ('Advanced', {'fields': ('attributes', 'created_at', 'updated_at')}),
        )

    def thumbnail_preview(self, obj):
        try:
            if obj and getattr(obj, 'thumbnail_url', None):
                url = str(obj.thumbnail_url).strip()
                if url:
                    return format_html('<img src="{}" style="max-height:100px;" />', url)
        except Exception:
            pass
        return '-'

    thumbnail_preview.short_description = 'Thumbnail'

    def preview_video_link(self, obj):
        try:
            if obj and getattr(obj, 'preview_video_url', None):
                url = str(obj.preview_video_url).strip()
                if url:
                    return format_html('<a href="{}" target="_blank">Preview video</a>', url)
        except Exception:
            pass
        return '-'

    preview_video_link.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not getattr(settings, 'R2_ENABLED', False):
            return
        has_thumb = bool(form.cleaned_data.get('upload_thumbnail'))
        has_video = bool(form.cleaned_data.get('upload_preview_video'))
        logger.info("[R2] ProductAdmin.save_model: obj_id=%s has_thumb=%s has_video=%s", obj.id, has_thumb, has_video)
        updated = False
        if has_thumb:
            f = form.cleaned_data['upload_thumbnail']
            key = build_object_key('products', obj.id, f.name, 'thumbnail')
            f.seek(0)
            obj.thumbnail_url = upload_file_to_r2(f, key, f.content_type)
            updated = True
        if form.cleaned_data.get('upload_preview_video'):
            f = form.cleaned_data['upload_preview_video']
            key = build_object_key('products', obj.id, f.name, 'preview')
            f.seek(0)
            obj.preview_video_url = upload_file_to_r2(f, key, f.content_type)
            updated = True
        if updated:
            obj.save(update_fields=['thumbnail_url', 'preview_video_url'])
            logger.info("[R2] ProductAdmin.save_model: R2 uploads completed for product %s", obj.id)
        elif has_thumb or has_video:
            logger.warning("[R2] ProductAdmin.save_model: upload fields present but no update (form.cleaned_data mismatch?)")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'category')
    list_filter = ('category',)
    raw_id_fields = ('product', 'category')
    ordering = ('product', 'category')


@admin.register(ProductModule)
class ProductModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'title', 'order_index', 'created_at')
    list_filter = ('product',)
    search_fields = ('title',)
    raw_id_fields = ('product',)
    readonly_fields = ('created_at',)
    ordering = ('product', 'order_index')


class LessonInline(admin.StackedInline):
    """Inline for adding/editing Lesson when creating/editing Product Content."""
    model = Lesson
    form = LessonAdminForm
    fk_name = 'product_content'
    max_num = 1
    min_num = 0
    extra = 1
    verbose_name = 'Lesson content'
    verbose_name_plural = 'Lesson content'
    can_delete = True

    def get_fieldsets(self, request, obj=None):
        r2_enabled = getattr(settings, 'R2_ENABLED', False)
        media_fields = (
            'lesson_type', 'duration_seconds',
            'upload_video', 'video_url',
            'upload_pdf', 'pdf_url',
            'upload_ppt', 'ppt_url',
        ) if r2_enabled else (
            'lesson_type', 'duration_seconds',
            'video_url', 'pdf_url', 'ppt_url',
        )
        return (
            (None, {'fields': media_fields}),
        )


class AssessmentInline(admin.StackedInline):
    """Inline for adding/editing Assessment when creating/editing Product Content."""
    model = Assessment
    fk_name = 'product_content'
    max_num = 1
    min_num = 0
    extra = 1
    verbose_name = 'Assessment content'
    verbose_name_plural = 'Assessment content'
    fields = ('pass_percentage',)
    can_delete = True


class AssessmentQuestionInline(admin.TabularInline):
    """Inline for adding questions when editing an Assessment."""
    model = AssessmentQuestion
    extra = 1
    fields = ('question_text',)


@admin.register(ProductContent)
class ProductContentAdmin(admin.ModelAdmin):
    form = ProductContentAdminForm
    list_display = ('id', 'product', 'module', 'content_type', 'title', 'order_index', 'is_mandatory', 'created_at')
    list_filter = ('content_type', 'product')
    search_fields = ('title',)
    raw_id_fields = ('product', 'module')
    readonly_fields = ('created_at',)
    ordering = ('product', 'order_index')
    inlines = [LessonInline, AssessmentInline]

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model != Lesson:
            return
        if not getattr(settings, 'R2_ENABLED', False):
            return
        for f in formset.forms:
            if not f.cleaned_data or f.cleaned_data.get('DELETE') or not getattr(f.instance, 'pk', None):
                continue
            obj = f.instance
            updated = False
            update_fields = []
            if f.cleaned_data.get('upload_video'):
                file_obj = f.cleaned_data['upload_video']
                file_obj.seek(0)
                key = build_object_key('lessons', obj.id, file_obj.name, 'video')
                obj.video_url = upload_file_to_r2(file_obj, key, file_obj.content_type)
                update_fields.append('video_url')
                updated = True
            if f.cleaned_data.get('upload_pdf'):
                file_obj = f.cleaned_data['upload_pdf']
                file_obj.seek(0)
                key = build_object_key('lessons', obj.id, file_obj.name, 'handout')
                obj.pdf_url = upload_file_to_r2(file_obj, key, file_obj.content_type)
                update_fields.append('pdf_url')
                updated = True
            if f.cleaned_data.get('upload_ppt'):
                file_obj = f.cleaned_data['upload_ppt']
                file_obj.seek(0)
                key = build_object_key('lessons', obj.id, file_obj.name, 'slides')
                obj.ppt_url = upload_file_to_r2(file_obj, key, file_obj.content_type)
                update_fields.append('ppt_url')
                updated = True
            if updated:
                obj.save(update_fields=update_fields)
                logger.info("[R2] ProductContentAdmin.save_formset: R2 uploads completed for lesson %s", obj.id)

    class Media:
        js = ('admin/js/product_content_inline_toggle.js',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ('id', 'product_content', 'lesson_type', 'duration_seconds', 'created_at')
    list_filter = ('lesson_type',)
    raw_id_fields = ('product_content',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_fieldsets(self, request, obj=None):
        r2_enabled = getattr(settings, 'R2_ENABLED', False)
        logger.info("[R2] LessonAdmin get_fieldsets: R2_ENABLED=%s (upload fields %s)", r2_enabled, "VISIBLE" if r2_enabled else "HIDDEN")
        media_fields = (
            'upload_video', 'video_url',
            'upload_pdf', 'pdf_url',
            'upload_ppt', 'ppt_url',
        ) if r2_enabled else ('video_url', 'pdf_url', 'ppt_url')
        return (
            (None, {'fields': ('product_content', 'lesson_type', 'duration_seconds')}),
            ('Media (upload or paste URL)', {'fields': media_fields}),
            (None, {'fields': ('created_at',)}),
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not getattr(settings, 'R2_ENABLED', False):
            return
        has_v = bool(form.cleaned_data.get('upload_video'))
        has_pdf = bool(form.cleaned_data.get('upload_pdf'))
        has_ppt = bool(form.cleaned_data.get('upload_ppt'))
        logger.info("[R2] LessonAdmin.save_model: obj_id=%s has_video=%s has_pdf=%s has_ppt=%s", obj.id, has_v, has_pdf, has_ppt)
        updated = False
        update_fields = []
        if has_v:
            f = form.cleaned_data['upload_video']
            key = build_object_key('lessons', obj.id, f.name, 'video')
            f.seek(0)
            obj.video_url = upload_file_to_r2(f, key, f.content_type)
            update_fields.append('video_url')
            updated = True
        if has_pdf:
            f = form.cleaned_data['upload_pdf']
            key = build_object_key('lessons', obj.id, f.name, 'handout')
            f.seek(0)
            obj.pdf_url = upload_file_to_r2(f, key, f.content_type)
            update_fields.append('pdf_url')
            updated = True
        if has_ppt:
            f = form.cleaned_data['upload_ppt']
            key = build_object_key('lessons', obj.id, f.name, 'slides')
            f.seek(0)
            obj.ppt_url = upload_file_to_r2(f, key, f.content_type)
            update_fields.append('ppt_url')
            updated = True
        if updated:
            obj.save(update_fields=update_fields)
            logger.info("[R2] LessonAdmin.save_model: R2 uploads completed for lesson %s", obj.id)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_content', 'pass_percentage', 'created_at')
    raw_id_fields = ('product_content',)
    readonly_fields = ('created_at', 'csv_import_link')
    fields = ('product_content', 'pass_percentage', 'csv_import_link', 'created_at')
    ordering = ('-created_at',)
    inlines = [AssessmentQuestionInline]

    def csv_import_link(self, obj):
        if obj and obj.pk:
            url = reverse('admin:admin_app_assessment_import_csv', kwargs={'object_id': obj.pk})
            return format_html(
                '<a class="button" href="{}">Upload CSV (questions &amp; options)</a>'
                '<p class="help">Replaces all existing questions and options for this assessment. '
                'Format: {}</p>',
                url,
                'question_number, question_text, option_order, option_text, is_correct',
            )
        return format_html(
            '<p class="help">Save the assessment first, then use the CSV upload button.</p>'
        )

    csv_import_link.short_description = 'Bulk import from CSV'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/import-csv/',
                self.admin_site.admin_view(self.import_csv_view),
                name='admin_app_assessment_import_csv',
            ),
        ]
        return custom + urls

    def import_csv_view(self, request, object_id):
        assessment = get_object_or_404(Assessment, pk=object_id)
        if not self.has_change_permission(request, assessment):
            raise PermissionDenied
        if request.method == 'POST':
            upload = request.FILES.get('csv_file')
            if not upload:
                self.message_user(request, 'Choose a CSV file to upload.', level=messages.ERROR)
            else:
                try:
                    nq, no = replace_assessment_questions_from_csv_file(assessment, upload)
                    self.message_user(
                        request,
                        f'Imported {nq} question(s) and {no} option(s).',
                        level=messages.SUCCESS,
                    )
                    return redirect(
                        reverse('admin:admin_app_assessment_change', args=[object_id])
                    )
                except ValidationError as e:
                    msg = '; '.join(str(m) for m in e.messages)
                    self.message_user(request, msg, level=messages.ERROR)
                except Exception:
                    logger.exception('Assessment CSV import failed for assessment %s', object_id)
                    self.message_user(
                        request,
                        'Import failed. Check CSV format and server logs.',
                        level=messages.ERROR,
                    )
            return redirect(reverse('admin:admin_app_assessment_import_csv', args=[object_id]))

        context = {
            **self.admin_site.each_context(request),
            'title': 'Import assessment questions (CSV)',
            'assessment': assessment,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, assessment),
        }
        return render(request, 'admin/assessment_import_csv.html', context)


class AssessmentOptionInline(admin.TabularInline):
    model = AssessmentOption
    extra = 0
    raw_id_fields = ()


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment', 'question_preview', 'created_at')
    list_filter = ('assessment',)
    raw_id_fields = ('assessment',)
    readonly_fields = ('created_at',)
    inlines = [AssessmentOptionInline]
    ordering = ('assessment', 'id')

    def question_preview(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text

    question_preview.short_description = 'Question'


@admin.register(AssessmentOption)
class AssessmentOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option_preview', 'is_correct', 'created_at')
    list_filter = ('is_correct',)
    raw_id_fields = ('question',)
    readonly_fields = ('created_at',)
    ordering = ('question', 'id')

    def option_preview(self, obj):
        return obj.option_text[:60] + '...' if len(obj.option_text) > 60 else obj.option_text

    option_preview.short_description = 'Option'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'created_at')
    list_filter = ('product',)
    raw_id_fields = ('user', 'product')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'final_price', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('billing_name', 'payment_gateway_order_id', 'payment_gateway_payment_id')
    raw_id_fields = ('user', 'product')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(CourseOwnership)
class CourseOwnershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'order', 'purchased_at', 'created_at')
    list_filter = ('course',)
    raw_id_fields = ('user', 'course', 'order')
    readonly_fields = ('created_at',)
    ordering = ('-purchased_at',)


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_content', 'completed_at', 'created_at')
    list_filter = ('product_content',)
    raw_id_fields = ('user', 'product_content')
    readonly_fields = ('created_at',)
    ordering = ('-completed_at',)


@admin.register(UserAssessmentResult)
class UserAssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_content', 'passed', 'score_percentage', 'created_at')
    list_filter = ('passed',)
    raw_id_fields = ('user', 'product_content')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
