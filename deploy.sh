#!/bin/bash
#
# Deploy quantum-edu-admin to AWS EC2 staging (same instance as Spring Boot BE).
# Run from quantum-edu-admin directory: ./deploy.sh
#
# Prerequisites:
#   1. cp deploy.env.example deploy.env; edit deploy.env
#   2. admin_django database created on RDS (see docs/DJANGO_AWS_DEPLOYMENT_GUIDE.md)
#   3. Superuser created (first-time only)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[deploy]${NC} $1"; }
warn() { echo -e "${YELLOW}[deploy]${NC} $1"; }
err() { echo -e "${RED}[deploy]${NC} $1"; exit 1; }

if [[ ! -f deploy.env ]]; then
  err "deploy.env not found. cp deploy.env.example deploy.env and edit it."
fi

set -a
source deploy.env
set +a

for var in EC2_HOST EC2_USER SSH_KEY RDS_ENDPOINT RDS_DB RDS_USER RDS_PASS DJANGO_SECRET_KEY ALLOWED_HOSTS; do
  if [[ -z "${!var}" ]]; then
    err "Missing required variable in deploy.env: $var"
  fi
done

SSH_KEY="${SSH_KEY/#\~/$HOME}"
if [[ ! -f "$SSH_KEY" ]]; then
  err "SSH key not found: $SSH_KEY"
fi

log "Syncing code to EC2..."
rsync -avz --delete \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'staticfiles' \
  --exclude '.env' \
  --exclude 'deploy.env' \
  --exclude 'gunicorn.env' \
  --exclude 'db.sqlite3' \
  . \
  "${EC2_USER}@${EC2_HOST}:~/quantum_edu_admin/"

log "Running deployment on EC2..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_HOST}" bash -s << REMOTE_SCRIPT
set -e
cd ~/quantum_edu_admin

echo "[EC2] Creating venv if needed..."
if [[ ! -f .venv/bin/activate ]] || [[ ! -x .venv/bin/python3 ]]; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv
  rm -rf .venv
  python3 -m venv .venv
fi
if [[ ! -f .venv/bin/activate ]]; then
  echo "[EC2] venv is still incomplete after python3 -m venv. Install python3-venv and retry." >&2
  exit 1
fi
source .venv/bin/activate

echo "[EC2] Native packages for mysqlclient (Django MySQL backend)..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  default-libmysqlclient-dev pkg-config build-essential python3-dev

echo "[EC2] Installing dependencies..."
pip install -q -r requirements.txt

echo "[EC2] Writing gunicorn.env..."
cat > gunicorn.env << GUNICORN_ENV
PYTHONUNBUFFERED=1
DJANGO_SETTINGS_MODULE=quantum_admin.settings.staging
MYSQL_HOST=${RDS_ENDPOINT}
MYSQL_PORT=3306
MYSQL_USER=${RDS_USER}
MYSQL_PASSWORD=${RDS_PASS}
MYSQL_DATABASE=${RDS_DB}
MYSQL_ADMIN_DB=admin_django
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
ALLOWED_HOSTS=${ALLOWED_HOSTS}
R2_ACCOUNT_ID=${R2_ACCOUNT_ID:-}
R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID:-}
R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY:-}
R2_BUCKET_NAME=${R2_BUCKET_NAME:-quantum-edu-media}
R2_PUBLIC_URL=${R2_PUBLIC_URL:-}
GUNICORN_ENV

echo "[EC2] Collecting static files..."
set -a
source gunicorn.env
set +a
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "[EC2] Installing/updating systemd unit if needed..."
sudo cp -f docs/quantum-edu-admin.service /etc/systemd/system/quantum-edu-admin.service 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true

echo "[EC2] Restarting Gunicorn..."
sudo systemctl restart quantum-edu-admin 2>/dev/null || echo "[EC2] Service not yet configured - run: sudo systemctl enable quantum-edu-admin && sudo systemctl start quantum-edu-admin"

echo "[EC2] Done."
REMOTE_SCRIPT

log "Deploy complete."
log "Admin URL: http://${EC2_HOST}:8000/admin/"
