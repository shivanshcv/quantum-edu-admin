# Django Admin — AWS EC2 Deployment Guide

**Production:** use **`./deploy.prod.sh`** with **`deploy.prod.env`**. Full AWS + nginx steps: **`quantum-edu-be/docs/AWS_PRODUCTION_GUIDE.md`**.

Deploy `quantum-edu-admin` on the **same EC2 instance** as your Spring Boot backend. Django runs on port **8000**; Spring Boot on **8080**.

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Prerequisites](#2-prerequisites)
3. [First-Time Setup on EC2](#3-first-time-setup-on-ec2)
4. [Create admin_django Database on RDS](#4-create-admin_django-database-on-rds)
5. [First Deploy and Superuser](#5-first-deploy-and-superuser)
6. [Configure Gunicorn (Systemd)](#6-configure-gunicorn-systemd)
7. [Open Port 8000](#7-open-port-8000)
8. [Redeploy with deploy.sh](#8-redeploy-with-deploysh)
9. [Access in Browser](#9-access-in-browser)
10. [HTTPS (Cloudflare Tunnel)](#10-https-cloudflare-tunnel-optional)

---

## 1. Architecture

| Service       | Port | URL                      |
|---------------|------|--------------------------|
| Spring Boot   | 8080 | http://EC2_IP:8080       |
| Django Admin  | 8000 | http://EC2_IP:8000/admin |

---

## 2. Prerequisites

- [ ] Spring Boot backend already running on EC2
- [ ] RDS MySQL with `quantum_education` database
- [ ] SSH access to EC2 working
- [ ] `deploy.env` created from `deploy.env.example`
- [ ] (Optional) Cloudflare R2 credentials — required for media uploads in admin (thumbnails, videos, PDFs)

---

## 3. First-Time Setup on EC2

SSH to EC2 and run:

```bash
ssh -i ~/Downloads/cli-admin.pem ubuntu@65.0.74.204

# Install Python 3 and venv
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Install MySQL client (for creating admin_django DB)
sudo apt install -y mysql-client

# Create app directory
mkdir -p ~/quantum_edu_admin
```

---

## 4. Create admin_django Database on RDS

From EC2 (replace with your RDS credentials):

```bash
mysql -h quantum-education-mysql-staging.chwqqisos58h.ap-south-1.rds.amazonaws.com \
  -P 3306 -u admin -p \
  -e "CREATE DATABASE IF NOT EXISTS admin_django CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Enter your RDS password when prompted.

**Tables:** Django creates its tables via `python manage.py migrate` (Step 5.3). For raw SQL reference, see [setup-admin-django-tables.sql](./setup-admin-django-tables.sql).

---

## 5. First Deploy and Superuser

**Note:** The `admin_django` database needs Django's tables (auth_user, sessions, etc.) before you can log in. Run `python manage.py migrate` once during first-time setup (see Step 5.3). Tables in `quantum_education` are managed by schema.sql, not Django migrations.

### 5.1 Create deploy.env

```bash
cd /Users/shivanshkumar/Documents/repos/quantum-edu-admin
cp deploy.env.example deploy.env
# Edit deploy.env with RDS_PASS, DJANGO_SECRET_KEY, EC2_HOST, ALLOWED_HOSTS
# For media uploads (admin thumbnails, videos, PDFs), add R2 credentials (see Section 5.1b)
```

### 5.1b Cloudflare R2 (Media Uploads) — Optional

To enable file uploads in the admin (product thumbnails, preview videos, lesson videos/PDFs/PPTs):

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → **Manage R2 API Tokens**
2. Click **Create API token** → choose **Object Read & Write** → Create
3. You get **two values** (save them; secret is shown only once):
   - **Access Key ID**: exactly **32 characters** (alphanumeric, no `cf_` or `cfut_` prefix)
   - **Secret Access Key**: **64 characters**
4. **Important**: Use R2 API token credentials only. Do NOT use Cloudflare API tokens (`cf_` or `cfut_` prefix) — those are for Cloudflare REST API, not R2 S3.
5. Create an R2 bucket (e.g. `quantum-edu-media`) and enable public access; note the public URL.
6. Add to `deploy.env`:

```bash
R2_ACCOUNT_ID=your-account-id          # 32-char hex, from Dashboard URL
R2_ACCESS_KEY_ID=your-access-key      # Must be 32 chars (R2 API token)
R2_SECRET_ACCESS_KEY=your-secret-key   # Must be 64 chars (R2 API token)
R2_BUCKET_NAME=quantum-edu-media
R2_PUBLIC_URL=https://pub-xxxx.r2.dev   # Public bucket URL from R2 settings
```

5. Redeploy: `./deploy.sh`

Without R2 credentials, the admin shows URL-only fields (paste links); with R2, upload fields appear.

### 5.2 Run First Deploy

```bash
./deploy.sh
```

### 5.3 Create Django Tables and Superuser (One-Time)

SSH to EC2 and run (creates Django tables in admin_django, then superuser):

```bash
cd ~/quantum_edu_admin
source .venv/bin/activate

export DJANGO_SETTINGS_MODULE=quantum_admin.settings.staging
export MYSQL_HOST=quantum-education-mysql-staging.chwqqisos58h.ap-south-1.rds.amazonaws.com
export MYSQL_PORT=3306
export MYSQL_USER=admin
export MYSQL_PASSWORD=YOUR_RDS_PASSWORD
export MYSQL_DATABASE=quantum_education
export MYSQL_ADMIN_DB=admin_django
export DJANGO_SECRET_KEY=YOUR_DJANGO_SECRET
export ALLOWED_HOSTS=65.0.74.204,localhost

# One-time: create Django tables in admin_django
python manage.py migrate --noinput

# Create admin user
python manage.py createsuperuser
# Enter username, email, password
```

### 5.4 Start Gunicorn Manually (Test Before Systemd)

```bash
cd ~/quantum_edu_admin
source .venv/bin/activate

# Use gunicorn.env from deploy (run ./deploy.sh first), or export vars manually:
set -a && source gunicorn.env 2>/dev/null || true && set +a
# If gunicorn.env doesn't exist yet, export manually:
# export MYSQL_HOST=... MYSQL_PASSWORD=... etc.

gunicorn --bind 0.0.0.0:8000 quantum_admin.wsgi:application
```

Open `http://65.0.74.204:8000/admin/` in your browser. Log in with the superuser. Press Ctrl+C to stop.

---

## 6. Configure Gunicorn (Systemd)

Deploy script (`./deploy.sh`) writes `~/quantum_edu_admin/gunicorn.env` from `deploy.env` and deploys `docs/quantum-edu-admin.service` to systemd on each run. Run `./deploy.sh` first, then enable and start (one-time):

```bash
sudo systemctl daemon-reload
sudo systemctl enable quantum-edu-admin
sudo systemctl start quantum-edu-admin
sudo systemctl status quantum-edu-admin
```

---

## 7. Open Port 8000

1. **EC2** → **Security Groups** → your instance's SG
2. **Edit inbound rules** → **Add rule**
3. **Type:** Custom TCP, **Port:** 8000, **Source:** 0.0.0.0/0
4. **Save**

---

## 8. Redeploy with deploy.sh

After first-time setup, redeploy with:

```bash
cd /Users/shivanshkumar/Documents/repos/quantum-edu-admin
./deploy.sh
```

The script syncs code, collects static files, and restarts the service. Tables are managed manually; migrations are not run automatically.

---

## 9. Access in Browser

| URL | Purpose |
|-----|---------|
| **http://65.0.74.204:8000/admin/** | Django admin login |

Replace `65.0.74.204` with your EC2 IP. Log in with the superuser you created.

---

## 10. HTTPS (Cloudflare Tunnel) — Optional

If you want HTTPS for the admin panel (e.g. to avoid mixed content or for security):

**Quick test** (stops when SSH disconnects):
```bash
# On EC2 - for Django admin (8000)
cloudflared tunnel --url http://localhost:8000
```

**Run as a systemd service** (keeps running after SSH disconnect):
See [CLOUDFLARE_TUNNEL_EC2_SERVICE.md](./CLOUDFLARE_TUNNEL_EC2_SERVICE.md) for setup. The default service exposes **Spring Boot (8080)**. For Django admin, use `--url http://localhost:8000` instead. Add the tunnel URL to `ALLOWED_HOSTS` (Django) or `APP_CORS_ORIGINS` (Spring Boot) and redeploy.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 / Connection refused | Check `sudo systemctl status quantum-edu-admin`; check logs: `journalctl -u quantum-edu-admin -f` |
| DB connection error | Verify RDS security group allows 3306 from EC2 SG |
| ALLOWED_HOSTS | Add your EC2 IP and any domain/tunnel URL to ALLOWED_HOSTS |
| Port 8000 not reachable | Open port 8000 in EC2 Security Group |
| No upload fields in admin | Add R2 credentials to `deploy.env` (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY), then redeploy. See Section 5.1b. |
| 500 on Product edit page | Check logs: `journalctl -u quantum-edu-admin -n 100`. Often caused by `product_category` table missing `id` column — run `quantum-edu-be/docs/migrations/add-product-category-id.sql` on RDS. |
| rsync not found | Use `scp -r` instead, or install rsync: `brew install rsync` (Mac) |

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy | `./deploy.sh` |
| Logs | `ssh ... 'journalctl -u quantum-edu-admin -f'` |
| Restart | `ssh ... 'sudo systemctl restart quantum-edu-admin'` |
| Admin URL | `http://EC2_IP:8000/admin/` |
