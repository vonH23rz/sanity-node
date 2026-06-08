#!/usr/bin/env sh
set -eu

APP_ROOT="${SANITY_NODE_APP_ROOT:-/app}"
CONFIG_PATH="${SANITY_NODE_CONFIG:-${APP_ROOT}/config/config.yaml}"
OUTPUT_PATH="${SANITY_NODE_OUTPUT:-${APP_ROOT}/html/index.html}"
LOG_FILE="${SANITY_NODE_LOG:-${APP_ROOT}/logs/generator.log}"

HTML_DIR="$(dirname -- "$OUTPUT_PATH")"
LOG_DIR="$(dirname -- "$LOG_FILE")"
WEB_DIR="${APP_ROOT}/web"
SCRIPTS_DIR="${APP_ROOT}/scripts"

VALIDATOR="${SCRIPTS_DIR}/validate-config.py"
PREFLIGHT="${SCRIPTS_DIR}/startup-preflight.py"
GENERATOR="${SCRIPTS_DIR}/generate-dashboard.py"

PORT="${SANITY_NODE_PORT:-8099}"
REFRESH_SECONDS="${SANITY_NODE_REFRESH_SECONDS:-300}"
RUN_UID="${PUID:-1000}"
RUN_GID="${PGID:-1000}"


fail() {
  echo "ERROR: $*" >&2
  exit 1
}


require_unsigned_integer() {
  name="$1"
  value="$2"

  case "$value" in
    ""|*[!0-9]*)
      fail "$name must be an unsigned integer; received: $value"
      ;;
  esac
}


validate_runtime_values() {
  require_unsigned_integer "SANITY_NODE_PORT" "$PORT"
  require_unsigned_integer \
    "SANITY_NODE_REFRESH_SECONDS" \
    "$REFRESH_SECONDS"
  require_unsigned_integer "PUID" "$RUN_UID"
  require_unsigned_integer "PGID" "$RUN_GID"

  if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    fail "SANITY_NODE_PORT must be between 1 and 65535"
  fi

  if [ "$REFRESH_SECONDS" -lt 1 ]; then
    fail "SANITY_NODE_REFRESH_SECONDS must be at least 1"
  fi
}


setup_files() {
  mkdir -p "$HTML_DIR" "$LOG_DIR"

  if [ -d "$WEB_DIR" ]; then
    cp -a "$WEB_DIR"/. "$HTML_DIR"/
  fi
}


validate_runtime_values

if [ "${1:-}" != "run" ]; then
  setup_files

  if [ "$(id -u)" = "0" ]; then
    if ! getent group "$RUN_GID" >/dev/null 2>&1; then
      groupadd -g "$RUN_GID" sanitynode
    fi

    if ! getent passwd "$RUN_UID" >/dev/null 2>&1; then
      useradd \
        -u "$RUN_UID" \
        -g "$RUN_GID" \
        -d /tmp \
        -s /usr/sbin/nologin \
        sanitynode
    fi

    chown -R "$RUN_UID:$RUN_GID" "$HTML_DIR" "$LOG_DIR"

    exec gosu "$RUN_UID:$RUN_GID" "$0" run
  fi

  exec "$0" run
fi


for required_file in "$VALIDATOR" "$PREFLIGHT" "$GENERATOR"; do
  if [ ! -x "$required_file" ]; then
    fail "required executable is missing: $required_file"
  fi
done


echo "[$(date -Iseconds)] Validating Sanity Node configuration"
"$VALIDATOR" "$CONFIG_PATH"

echo "[$(date -Iseconds)] Running Sanity Node startup preflight"
"$PREFLIGHT" \
  --config "$CONFIG_PATH" \
  --output "$OUTPUT_PATH" \
  --log "$LOG_FILE"


generate_once() {
  echo "[$(date -Iseconds)] Running Sanity Node generator"

  if ! "$GENERATOR" >> "$LOG_FILE" 2>&1; then
    echo \
      "[$(date -Iseconds)] Generator failed; see $LOG_FILE" \
      >&2
    return 1
  fi

  if [ ! -s "$OUTPUT_PATH" ]; then
    echo \
      "[$(date -Iseconds)] Generator returned success but did not create a nonempty dashboard: $OUTPUT_PATH" \
      >&2
    return 1
  fi

  echo "[$(date -Iseconds)] Generator finished successfully"
}


# Never allow a stale dashboard to make a failed first start appear healthy.
rm -f -- "$OUTPUT_PATH"

if ! generate_once; then
  fail "initial dashboard generation failed; web service was not started"
fi


generate_loop() {
  SLEEP_PID=""

  stop_generate_loop() {
    if [ -n "$SLEEP_PID" ]; then
      kill "$SLEEP_PID" 2>/dev/null || true
    fi

    exit 0
  }

  trap stop_generate_loop INT TERM

  while true; do
    sleep "$REFRESH_SECONDS" &
    SLEEP_PID="$!"

    if ! wait "$SLEEP_PID"; then
      exit 0
    fi

    SLEEP_PID=""

    if ! generate_once; then
      echo \
        "[$(date -Iseconds)] Keeping the last successfully generated dashboard" \
        >&2
    fi
  done
}


generate_loop &
GENERATOR_PID="$!"


cleanup() {
  kill "$GENERATOR_PID" 2>/dev/null || true
  wait "$GENERATOR_PID" 2>/dev/null || true
}


trap cleanup EXIT INT TERM

echo "[$(date -Iseconds)] Serving Sanity Node dashboard on port $PORT"
python3 -m http.server "$PORT" --directory "$HTML_DIR"
