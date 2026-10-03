# Quantum Education Admin Panel

## Overview

Django admin panel for managing the Quantum Education platform database. Shares the same MySQL server as the Spring Boot backend (`quantum-edu-be`), with a separate database for Django's auth and sessions.

## Database Architecture

| Database | Purpose | Managed By |
|----------|---------|------------|
| **admin_django** | Django auth_user, sessions, admin migrations | Django |
| **quantum_education** | Products, users, orders, LMS, etc. | Spring Boot (schema), Django (read/write via admin) |

## Why Two Databases?

- **auth_user conflict**: Django's default auth uses a table named `auth_user`. The Spring Boot app uses `auth_user` in `quantum_education` for application users. Using a separate `admin_django` database keeps Django's admin auth isolated.
- **Admin login**: Separate from the main app's JWT auth. Admin users are created via `createsuperuser` and stored in `admin_django.auth_user`.

## Database Router

`admin_app.db_router.QuantumEducationRouter` routes all `admin_app` models to `quantum_education`. Django's built-in apps (auth, sessions) use `default` (admin_django).

## Environment Settings

| File | Use Case |
|------|----------|
| `settings/dev.py` | Local development (localhost MySQL) |
| `settings/staging.py` | Aiven MySQL (staging) |
| `settings/prod.py` | Production MySQL |

## Schema Notes

- **Unmanaged models**: All `admin_app` models have `managed = False`. Django does not create or alter these tables.
- **product_category**: Includes `id` column for Django admin. Existing DBs run `quantum-edu-be/docs/migrations/add-product-category-id.sql`. Spring Boot uses product_id/category_id only; no changes needed.

## Admin Flow: Adding Product Content

When adding a **Product Content**, you can add its actual content (Lesson or Assessment) in the same form:

1. **Product Content + Lesson (one screen):** Select content type `LESSON`, fill Product Content fields, then add the Lesson in the "Lesson content" inline (lesson type, duration, video/PDF/PPT upload or URL). Save once.
2. **Product Content + Assessment (one screen):** Select content type `ASSESSMENT`, fill Product Content fields, then add the Assessment in the "Assessment content" inline (pass percentage). Save. To add questions and options, edit the Assessment and add questions (each question can be edited to add options).
