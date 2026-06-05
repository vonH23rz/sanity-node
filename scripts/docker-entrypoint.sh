#!/usr/bin/env sh
set -eu

HTML_DIR="/app/html"
LOG_DIR="/app/logs"
WEB_DIR="/app/web"
PORT="${SANITY_NODE_PORT:-8099}"
REFRESH_SECONDS="${SANITY_NODE_REFRESH_SECONDS:-300}"

setup_files() {
  mkdir -p "$HTML_DIR" "$LOG_DIR"

  if [ -d "$WEB_DIR" ]; then
    cp -a "$WEB_DIR"/. "$HTML_DIR"/
  fi
}

if [ "${1:-}" != "run" ]; then
  setup_files

  if [ "$(id -u)" = "0" ]; then
    RUN_UID="${PUID:-1000}"
    RUN_GID="${PGID:-1000}"

    if ! getent group "$RUN_GID" >/dev/null 2>&1; then
      groupadd -g "$RUN_GID" sanitynode
    fi

    if ! getent passwd "$RUN_UID" >/dev/null 2>&1; then
      useradd -u "$RUN_UID" -g "$RUN_GID" -d /tmp -s /usr/sbin/nologin sanitynode
    fi

    chown -R "$RUN_UID:$RUN_GID" "$HTML_DIR" "$LOG_DIR"

    exec gosu "$RUN_UID:$RUN_GID" "$0" run
  fi

  exec "$0" run
fi

generate_once() {
  echo "[$(date -Iseconds)] Running Sanity Node generator"
  if /app/scripts/generate-dashboard.py >> "$LOG_DIR/generator.log" 2>&1; then
    echo "[$(date -Iseconds)] Generator finished successfully"
  else
    echo "[$(date -Iseconds)] Generator failed; see $LOG_DIR/generator.log" >&2
  fi
}

generate_loop() {
  while true; do
    generate_once
    sleep "$REFRESH_SECONDS"
  done
}

generate_loop &
GENERATOR_PID="$!"

trap 'kill "$GENERATOR_PID" 2>/dev/null || true' INT TERM

echo "[$(date -Iseconds)] Serving Sanity Node dashboard on port $PORT"
python3 -m http.server "$PORT" --directory "$HTML_DIR"
