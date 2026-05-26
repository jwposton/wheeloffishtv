#!/bin/sh
set -e

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

# LinuxServer-style: start as root, align the app user with PUID/PGID, fix /data ownership, drop privileges.
if [ "$(id -u)" = "0" ]; then
  groupmod -o -g "$PGID" app
  usermod -o -u "$PUID" -g app app
  mkdir -p /data/artwork
  chown -R app:app /data
  exec su app -s /bin/sh -c 'exec "$0" "$@"' -- "$0" "$@"
fi

alembic upgrade head
exec uvicorn wheeloffish.main:app --host 0.0.0.0 --port 8000
