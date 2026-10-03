-- Create admin_django database for Django auth, sessions, and admin.
-- Run: mysql -u root -p < setup-admin-django-db.sql
-- Or: mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS admin_django CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

CREATE DATABASE IF NOT EXISTS admin_django
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
