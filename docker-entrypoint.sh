#!/bin/sh
# Container start: wait for MySQL, create/upgrade Django's own tables in admin_django,
# ensure the configured admin accounts exist, then run the CMD (gunicorn).
set -e

echo "[admin] Waiting for database..."
i=0
until python manage.py shell -c "from django.db import connections; [connections[a].ensure_connection() for a in ('default', 'quantum_education')]" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    echo "[admin] Database not reachable after 60s" >&2
    python manage.py shell -c "from django.db import connections; connections['default'].ensure_connection()"
    exit 1
  fi
  sleep 2
done

echo "[admin] Applying Django migrations (admin_django only)"
python manage.py migrate --database=default --noinput

python manage.py ensure_admin_users

exec "$@"
