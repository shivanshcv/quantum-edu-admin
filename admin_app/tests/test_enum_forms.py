"""Unit tests for admin enum ChoiceFields (aligned with quantum-edu-be JPA enums)."""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from admin_app.forms import (
    DIFFICULTY_LEVEL_CHOICES,
    LESSON_TYPE_CHOICES,
    PRODUCT_CONTENT_TYPE_CHOICES,
    LessonAdminForm,
    ProductAdminForm,
    ProductContentAdminForm,
)


class EnumChoicesTests(SimpleTestCase):
    def test_difficulty_level_values_match_backend(self):
        self.assertEqual(
            [c[0] for c in DIFFICULTY_LEVEL_CHOICES],
            ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'],
        )

    def test_product_content_type_values_match_backend(self):
        self.assertEqual(
            [c[0] for c in PRODUCT_CONTENT_TYPE_CHOICES],
            ['LESSON', 'ASSESSMENT'],
        )

    def test_lesson_type_values_match_backend(self):
        self.assertEqual(
            [c[0] for c in LESSON_TYPE_CHOICES],
            ['VIDEO', 'PDF', 'PPT'],
        )

    def test_product_difficulty_field_rejects_invalid(self):
        field = ProductAdminForm.base_fields['difficulty_level']
        field.clean('BEGINNER')
        field.clean('INTERMEDIATE')
        field.clean('ADVANCED')
        field.clean('')
        with self.assertRaises(ValidationError):
            field.clean('Easy')

    def test_product_content_type_field_rejects_invalid(self):
        field = ProductContentAdminForm.base_fields['content_type']
        field.clean('LESSON')
        field.clean('ASSESSMENT')
        with self.assertRaises(ValidationError):
            field.clean('QUIZ')

    def test_lesson_type_field_rejects_invalid(self):
        field = LessonAdminForm.base_fields['lesson_type']
        field.clean('VIDEO')
        field.clean('PDF')
        field.clean('PPT')
        with self.assertRaises(ValidationError):
            field.clean('AUDIO')
