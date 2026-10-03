#!/usr/bin/env python
"""E2E tests for Django admin using test client.
Run: python test_admin_e2e.py
Requires: superuser created (admin/admin123), quantum_education DB with data.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantum_admin.settings.dev')
django.setup()

from django.test import Client
from django.urls import reverse
from admin_app.models import Category, Product, ProductCategory

ALL_MODELS = [
    'authuser', 'userprofile', 'category', 'product', 'productcategory',
    'productmodule', 'productcontent', 'lesson', 'assessment',
    'assessmentquestion', 'assessmentoption', 'cartitem', 'order',
    'courseownership', 'userlessonprogress', 'userassessmentresult',
]


def main():
    client = Client()
    errors = []

    # 1. Login
    if not client.login(username='admin', password='admin123'):
        errors.append("Login failed")
        print("FAILED:", errors)
        return 1
    print("1. Login: OK")

    # 2. List views for all 16 models
    for model in ALL_MODELS:
        url = reverse(f'admin:admin_app_{model}_changelist')
        r = client.get(url)
        if r.status_code != 200:
            errors.append(f"List {model}: {r.status_code}")
    if not errors:
        print(f"2. List views (all {len(ALL_MODELS)} models): OK")

    # 3. Add Category
    r = client.post(reverse('admin:admin_app_category_add'), {
        'name': 'E2E Test Category',
        'slug': 'e2e-test-category',
        'level': 0,
        'is_active': 'on',
    })
    if r.status_code != 302:
        errors.append(f"Add Category: {r.status_code}")
    else:
        print("3. Add Category: OK")

    cat = Category.objects.get(slug='e2e-test-category')

    # 4. Add ProductCategory
    product = Product.objects.first()
    if product:
        r = client.post(reverse('admin:admin_app_productcategory_add'), {
            'product': str(product.id),
            'category': str(cat.id),
        })
        if r.status_code != 302:
            errors.append(f"Add ProductCategory: {r.status_code}")
        else:
            print("4. Add ProductCategory: OK")

    # 5. Edit Category
    r = client.post(reverse('admin:admin_app_category_change', args=[cat.id]), {
        'name': 'E2E Test Category Updated',
        'slug': 'e2e-test-category',
        'level': 0,
        'is_active': 'on',
        '_continue': 'Save and continue editing',
    })
    if r.status_code != 302:
        errors.append(f"Edit Category: {r.status_code}")
    else:
        print("5. Edit Category: OK")

    # 6. Delete ProductCategory
    pc = ProductCategory.objects.filter(category=cat).first()
    if pc:
        r = client.post(reverse('admin:admin_app_productcategory_delete', args=[pc.id]), {'post': 'yes'})
        if r.status_code != 302:
            errors.append(f"Delete ProductCategory: {r.status_code}")
        else:
            print("6. Delete ProductCategory: OK")

    # 7. Delete Category
    r = client.post(reverse('admin:admin_app_category_delete', args=[cat.id]), {'post': 'yes'})
    if r.status_code != 302:
        errors.append(f"Delete Category: {r.status_code}")
    else:
        print("7. Delete Category: OK")

    if errors:
        print("\nFAILED:", errors)
        return 1
    print("\nAll E2E tests passed.")
    return 0


if __name__ == '__main__':
    exit(main())
