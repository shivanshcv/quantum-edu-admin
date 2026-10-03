"""
Unmanaged Django models mapping to quantum_education database tables.
Django does not create or alter these tables; they are managed by the Spring Boot app.
"""
from django.db import models


class AuthUser(models.Model):
    """App users (quantum-edu-be auth_user). Not Django's auth.User."""
    email = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default='USER')
    is_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    email_verification_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'auth_user'
        verbose_name = 'Auth User'
        verbose_name_plural = 'Auth Users'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    billing_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    profile_image_url = models.CharField(max_length=500, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    gst_number = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, db_column='parent_id')
    level = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    short_description = models.TextField()
    long_description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    thumbnail_url = models.CharField(max_length=500, null=True, blank=True)
    preview_video_url = models.CharField(max_length=500, null=True, blank=True)
    difficulty_level = models.CharField(max_length=20, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    attributes = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.title


class ProductCategory(models.Model):
    """Links products to categories. Requires migration: quantum-edu-be/docs/migrations/add-product-category-id.sql"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')

    class Meta:
        managed = False
        db_table = 'product_category'
        unique_together = [['product', 'category']]
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return f"{self.product_id} - {self.category_id}"


class ProductModule(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    title = models.CharField(max_length=255)
    order_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'product_module'
        verbose_name_plural = 'Product Modules'

    def __str__(self):
        return self.title


class ProductContent(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    module = models.ForeignKey(ProductModule, on_delete=models.SET_NULL, null=True, blank=True, db_column='module_id')
    content_type = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    order_index = models.IntegerField()
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'product_content'
        verbose_name_plural = 'Product Contents'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    product_content = models.OneToOneField(
        ProductContent, on_delete=models.CASCADE, db_column='product_content_id'
    )
    lesson_type = models.CharField(max_length=10)
    video_url = models.CharField(max_length=500, null=True, blank=True)
    pdf_url = models.CharField(max_length=500, null=True, blank=True)
    ppt_url = models.CharField(max_length=500, null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'lesson'
        verbose_name_plural = 'Lessons'

    def __str__(self):
        return f"Lesson: {self.product_content_id}"


class Assessment(models.Model):
    product_content = models.OneToOneField(
        ProductContent, on_delete=models.CASCADE, db_column='product_content_id'
    )
    pass_percentage = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'assessment'
        verbose_name_plural = 'Assessments'

    def __str__(self):
        return f"Assessment: {self.product_content_id}"


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, db_column='assessment_id')
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'assessment_question'
        verbose_name_plural = 'Assessment Questions'

    def __str__(self):
        return self.question_text[:50] + '...' if len(self.question_text) > 50 else self.question_text


class AssessmentOption(models.Model):
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE, db_column='question_id')
    option_text = models.TextField()
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'assessment_option'
        verbose_name_plural = 'Assessment Options'

    def __str__(self):
        return self.option_text[:50] + '...' if len(self.option_text) > 50 else self.option_text


class CartItem(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'cart'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"Cart: user={self.user_id} product={self.product_id}"


class Order(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_name = models.CharField(max_length=255)
    billing_address_line1 = models.CharField(max_length=255)
    billing_address_line2 = models.CharField(max_length=255, null=True, blank=True)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_country = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_gst_number = models.CharField(max_length=30, null=True, blank=True)
    payment_gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
    payment_gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'orders'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.id}"


class CourseOwnership(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    course = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='course_id')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    purchased_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'course_ownership'
        verbose_name_plural = 'Course Ownerships'

    def __str__(self):
        return f"Ownership: user={self.user_id} course={self.course_id}"


class UserLessonProgress(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    product_content = models.ForeignKey(
        ProductContent, on_delete=models.CASCADE, db_column='product_content_id'
    )
    completed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'user_lesson_progress'
        verbose_name_plural = 'User Lesson Progress'

    def __str__(self):
        return f"Progress: user={self.user_id} content={self.product_content_id}"


class UserAssessmentResult(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, db_column='user_id')
    product_content = models.ForeignKey(
        ProductContent, on_delete=models.CASCADE, db_column='product_content_id'
    )
    passed = models.BooleanField()
    score_percentage = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'user_assessment_result'
        verbose_name_plural = 'User Assessment Results'

    def __str__(self):
        return f"Result: user={self.user_id} passed={self.passed}"
