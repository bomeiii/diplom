#!/bin/sh
set -e

MEDIA_DIR="${DJANGO_MEDIA_ROOT:-${RAILWAY_VOLUME_MOUNT_PATH:-/app/media}}"
mkdir -p "$MEDIA_DIR"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 120
