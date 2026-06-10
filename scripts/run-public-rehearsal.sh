#!/usr/bin/env bash

set -euo pipefail
umask 0002

REHEARSAL_ROOT="${SANITY_NODE_REHEARSAL_ROOT:-/opt/sanity-node-public-rehearsal}"
APP_ROOT="${SANITY_NODE_APP_ROOT:-${REHEARSAL_ROOT}/app}"
CONFIG_PATH="${SANITY_NODE_CONFIG:-${REHEARSAL_ROOT}/config/config.yaml}"
OUTPUT_PATH="${SANITY_NODE_OUTPUT:-${REHEARSAL_ROOT}/html/index.html}"
LOG_PATH="${SANITY_NODE_LOG:-${REHEARSAL_ROOT}/logs/generator.log}"
PROTECTED_ROOT="${SANITY_NODE_PROTECTED_ROOT:-/opt/homelab-dashboard}"

VALIDATOR="${APP_ROOT}/scripts/validate-config.py"
PREFLIGHT="${APP_ROOT}/scripts/startup-preflight.py"
GENERATOR="${APP_ROOT}/scripts/generate-dashboard.py"

RUN_DIR="${REHEARSAL_ROOT}/run"
LOCK_PATH="${RUN_DIR}/generator.lock"


canonical_path() {
    python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve(strict=False))
PY
}


path_is_within() {
    local parent="$1"
    local candidate="$2"

    case "$candidate" in
        "$parent"/*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}


paths_overlap() {
    local first="$1"
    local second="$2"

    [[ "$first" == "$second" ]] ||
        path_is_within "$first" "$second" ||
        path_is_within "$second" "$first"
}


emit() {
    local message
    message="[$(date -Iseconds)] $*"

    if [[ -n "${LOG_PATH:-}" ]] &&
       [[ -d "$(dirname -- "$LOG_PATH")" ]]; then
        printf '%s\n' "$message" | tee -a "$LOG_PATH"
    else
        printf '%s\n' "$message"
    fi
}


fail() {
    emit "ERROR: $*"
    exit 1
}


run_logged() {
    "$@" 2>&1 | tee -a "$LOG_PATH"
}


REHEARSAL_ROOT_CANON="$(canonical_path "$REHEARSAL_ROOT")"
APP_ROOT_CANON="$(canonical_path "$APP_ROOT")"
CONFIG_PATH_CANON="$(canonical_path "$CONFIG_PATH")"
OUTPUT_PATH_CANON="$(canonical_path "$OUTPUT_PATH")"
LOG_PATH_CANON="$(canonical_path "$LOG_PATH")"
PROTECTED_ROOT_CANON="$(canonical_path "$PROTECTED_ROOT")"

if [[ "$REHEARSAL_ROOT_CANON" == "/" ]]; then
    fail "rehearsal root must not be the filesystem root"
fi

if paths_overlap \
    "$REHEARSAL_ROOT_CANON" \
    "$PROTECTED_ROOT_CANON"
then
    fail "rehearsal root overlaps the protected production root"
fi

for isolated_path in \
    "$APP_ROOT_CANON" \
    "$CONFIG_PATH_CANON" \
    "$OUTPUT_PATH_CANON" \
    "$LOG_PATH_CANON"
do
    if ! path_is_within \
        "$REHEARSAL_ROOT_CANON" \
        "$isolated_path"
    then
        fail "runtime path escapes the rehearsal root: $isolated_path"
    fi

    if paths_overlap \
        "$isolated_path" \
        "$PROTECTED_ROOT_CANON"
    then
        fail "runtime path overlaps the protected production root: $isolated_path"
    fi
done

if [[ ! -f "$CONFIG_PATH" ]]; then
    fail "rehearsal configuration does not exist: $CONFIG_PATH"
fi

for required_file in \
    "$VALIDATOR" \
    "$PREFLIGHT" \
    "$GENERATOR"
do
    if [[ ! -x "$required_file" ]]; then
        fail "required executable is missing: $required_file"
    fi
done

mkdir -p \
    "$(dirname -- "$OUTPUT_PATH")" \
    "$(dirname -- "$LOG_PATH")" \
    "$RUN_DIR"

touch "$LOG_PATH"
chmod 0664 "$LOG_PATH"

exec 9>"$LOCK_PATH"

if ! flock -n 9; then
    fail "another public rehearsal generation is already running"
fi

start_epoch_ns="$(date +%s%N)"
temporary_output="${OUTPUT_PATH}.next.$$"

cleanup() {
    rm -f -- "$temporary_output"
}

trap cleanup EXIT INT TERM

emit "Starting Sanity Node public rehearsal generation"
emit "Application root: $APP_ROOT"
emit "Configuration: $CONFIG_PATH"
emit "Isolated output: $OUTPUT_PATH"

emit "Validating rehearsal configuration"

if ! run_logged "$VALIDATOR" "$CONFIG_PATH"; then
    fail "configuration validation failed"
fi

runtime_mode="$(
    python3 - "$CONFIG_PATH" <<'PY'
from pathlib import Path
import sys

import yaml

config = yaml.safe_load(
    Path(sys.argv[1]).read_text(encoding="utf-8")
) or {}

dashboard = (
    config.get("dashboard", {})
    if isinstance(config, dict)
    else {}
)

if not isinstance(dashboard, dict):
    dashboard = {}

print(
    str(dashboard.get("runtime_mode", ""))
    .strip()
    .lower()
)
PY
)"

if [[ "$runtime_mode" != "public" ]]; then
    fail "rehearsal configuration must set dashboard.runtime_mode: public"
fi

emit "Running startup preflight"

if ! run_logged \
    "$PREFLIGHT" \
    --config "$CONFIG_PATH" \
    --output "$OUTPUT_PATH" \
    --log "$LOG_PATH"
then
    fail "startup preflight failed"
fi

rm -f -- "$temporary_output"

emit "Running public dashboard generator"

if ! SANITY_NODE_CONFIG="$CONFIG_PATH" \
     SANITY_NODE_OUTPUT="$temporary_output" \
     SANITY_NODE_LOG="$LOG_PATH" \
     "$GENERATOR" 2>&1 |
     tee -a "$LOG_PATH"
then
    fail "dashboard generation failed"
fi

if [[ ! -s "$temporary_output" ]]; then
    fail "generator returned success without a nonempty dashboard"
fi

if ! grep -Fq \
    "Dashboard Summary" \
    "$temporary_output"
then
    fail "generated dashboard is missing the Dashboard Summary marker"
fi

if ! grep -Fq \
    "Runtime Detail" \
    "$temporary_output"
then
    fail "generated dashboard is missing the Runtime Detail marker"
fi

if grep -Fq \
    "Config Preview" \
    "$temporary_output"
then
    fail "generated public dashboard contains obsolete Config Preview wording"
fi

chmod 0664 "$temporary_output"
mv -f -- "$temporary_output" "$OUTPUT_PATH"

output_hash="$(
    sha256sum "$OUTPUT_PATH" |
        awk '{print $1}'
)"

finish_epoch_ns="$(date +%s%N)"

duration_seconds="$(
    awk \
        -v start="$start_epoch_ns" \
        -v finish="$finish_epoch_ns" \
        'BEGIN {
            printf "%.3f", (finish - start) / 1000000000
        }'
)"

emit "Public rehearsal generation completed successfully"
emit "Output SHA-256: $output_hash"
emit "Runtime seconds: $duration_seconds"

trap - EXIT INT TERM
