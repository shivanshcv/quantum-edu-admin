# Quantum Education Admin Panel

Django admin panel for managing Quantum Education database (products, courses, users, orders, etc.). Uses the same MySQL server as the Spring Boot backend, with a separate `admin_django` database for Django's auth and sessions.

## Architecture

| Database | Purpose |
|----------|---------|
| **admin_django** | Django auth_user, sessions, admin (Django-managed) |
| **quantum_education** | Business data: products, orders, users, etc. (Spring Boot-managed, read/write via admin) |

## Prerequisites

- Python 3.9+
- MySQL 8 (same as quantum-edu-be)
- Access to `quantum_education` database

> Uses PyMySQL (pure Python MySQL driver). For mysqlclient (faster, requires native build), see `requirements.txt` and install MySQL dev libraries.

## Setup

### 1. Create virtual environment

```bash
cd quantum-edu-admin
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create admin_django database

```bash
mysql -u root -p < docs/setup-admin-django-db.sql
```

Or manually:

```sql
CREATE DATABASE IF NOT EXISTS admin_django
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### 4. Run product_category migration (existing databases only)

If your `quantum_education` database was created with the old schema (composite PK on product_category), run once:

```bash
# From quantum-edu-be repo root:
mysql -u root -p quantum_education < docs/migrations/add-product-category-id.sql
```

Skip this if you used a fresh `schema.sql` from quantum-edu-be (it already has `id`).

### 5. Configure environment

Copy `.env.example` to `.env` and adjust if needed. Dev defaults work with local MySQL (root/root).

### 6. Run migrations (creates Django tables in admin_django only)

```bash
python manage.py migrate
```

This creates only Django's auth, sessions, and admin tables in `admin_django`. No changes are made to `quantum_education` tables.

### 7. Create superuser

```bash
python manage.py createsuperuser
```

### 8. Run server

```bash
python manage.py runserver 8000
```

Open http://localhost:8000/admin/ and log in.

## E2E Tests

```bash
# Requires: superuser (default test uses admin/admin123), quantum_education with products
python test_admin_e2e.py
```

Tests: login, list all 16 models, add/edit/delete Category, add/delete ProductCategory.

## Environments

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Module | `quantum_admin.settings.dev` | `quantum_admin.settings.staging` | `quantum_admin.settings.prod` |
| Run | `python manage.py runserver` | `DJANGO_SETTINGS_MODULE=quantum_admin.settings.staging python manage.py runserver` | Same with `prod` |

Set `DJANGO_SETTINGS_MODULE` in `.env` or export before running.

## Admin Models

16 tables from `quantum_education` are available:

- **Auth** – Auth User, User Profile
- **Catalog** – Category, Product, Product Category, Product Module, Product Content
- **Content** – Lesson, Assessment, Assessment Question, Assessment Option
- **Commerce** – Cart Item, Order, Course Ownership
- **LMS** – User Lesson Progress, User Assessment Result

**Product Category** is editable inline when editing a Product, or as a standalone model. Requires `add-product-category-id.sql` migration for existing databases.

## Project Structure

```
quantum-edu-admin/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── quantum_admin/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── staging.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── admin_app/
│   ├── models.py      # Unmanaged models for quantum_education tables
│   ├── admin.py       # Admin registrations
│   └── db_router.py    # Routes admin_app to quantum_education DB
└── docs/
    ├── setup-admin-django-db.sql
    └── ARCHITECTURE.md
```

## Phase 2: R2 Media Upload

Upload media from Django admin → Cloudflare R2 → URL stored in DB.

**Product:** thumbnail, preview video  
**Lesson:** video, PDF, PPT

Configure R2 in `.env` (see `.env.example`). Requires R2 API token from **Manage R2 API Tokens** (Access Key ID + Secret Access Key). See `quantum-edu-be/docs/R2_SETUP_GUIDE.md`.
