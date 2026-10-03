# Build stage: compile mysqlclient wheels
FROM python:3.12-slim AS build
WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Run stage
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=quantum_admin.settings.prod
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY --chown=app:app . .
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput \
    && chmod +x docker-entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
# PORT is injected by PaaS hosts such as Render; defaults to 8000 for docker compose.
CMD ["sh", "-c", "exec gunicorn quantum_admin.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 300 --access-logfile - --error-logfile -"]
