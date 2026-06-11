#!/usr/bin/env bash

set -euo pipefail
umask 0002

PRODUCTION_ROOT="${SANITY_NODE_PRODUCTION_ROOT:-/opt/sanity-node}"
APP_ROOT="${SANITY_NODE_APP_ROOT:-${PRODUCTION_ROOT}/app}"
CONFIG_PATH="${SANITY_NODE_CONFIG:-${PRODUCTION_ROOT}/config/config.yaml}"
OUTPUT_PATH="${SANITY_NODE_OUTPUT:-${PRODUCTION_ROOT}/html/index.html}"
LOG_PATH="${SANITY_NODE_LOG:-${PRODUCTION_ROOT}/logs/generator.log}"

REFERENCE_ROOT="${SANITY_NODE_REFERENCE_ROOT:-/opt/homelab-dashboard}"
REHEARSAL_ROOT="${SANITY_NODE_REHEARSAL_ROOT:-/opt/sanity-node-public-rehearsal}"

VALIDATOR="${APP_ROOT}/scripts/validate-config.py"
PREFLIGHT="${APP_ROOT}/scripts/startup-preflight.py"
GENERATOR="${APP_ROOT}/scripts/generate-dashboard.py"

RUN_DIR="${PRODUCTION_ROOT}/run"
LOCK_PATH="${RUN_DIR}/generator.lock"


canonical_path() {
    python3 - "$1" <<'PYTHON'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve(strict=False))
PYTHON
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


PRODUCTION_ROOT_CANON="$(canonical_path "$PRODUCTION_ROOT")"
APP_ROOT_CANON="$(canonical_path "$APP_ROOT")"
CONFIG_PATH_CANON="$(canonical_path "$CONFIG_PATH")"
OUTPUT_PATH_CANON="$(canonical_path "$OUTPUT_PATH")"
LOG_PATH_CANON="$(canonical_path "$LOG_PATH")"
RUN_DIR_CANON="$(canonical_path "$RUN_DIR")"
REFERENCE_ROOT_CANON="$(canonical_path "$REFERENCE_ROOT")"
REHEARSAL_ROOT_CANON="$(canonical_path "$REHEARSAL_ROOT")"

if [[ "$PRODUCTION_ROOT_CANON" == "/" ]]; then
    fail "production root must not be the filesystem root"
fi

protected_roots=(
    "$REFERENCE_ROOT_CANON"
    "$REHEARSAL_ROOT_CANON"
)

for protected_root in "${protected_roots[@]}"; do
    if paths_overlap \
        "$PRODUCTION_ROOT_CANON" \
        "$protected_root"
    then
        fail \
            "production root overlaps a protected runtime root: " \
            "$protected_root"
    fi
done

for production_path in \
    "$APP_ROOT_CANON" \
    "$CONFIG_PATH_CANON" \
    "$OUTPUT_PATH_CANON" \
    "$LOG_PATH_CANON" \
    "$RUN_DIR_CANON"
do
    if ! path_is_within \
        "$PRODUCTION_ROOT_CANON" \
        "$production_path"
    then
        fail "runtime path escapes the production root: $production_path"
    fi

    for protected_root in "${protected_roots[@]}"; do
        if paths_overlap \
            "$production_path" \
            "$protected_root"
        then
            fail \
                "runtime path overlaps a protected runtime root: " \
                "$production_path"
        fi
    done
done

if [[ ! -f "$CONFIG_PATH" ]]; then
    fail "production configuration does not exist: $CONFIG_PATH"
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
    fail "another public production generation is already running"
fi

start_epoch_ns="$(date +%s%N)"
temporary_output="${OUTPUT_PATH}.next.$$"

cleanup() {
    rm -f -- "$temporary_output"
}

trap cleanup EXIT INT TERM

emit "Starting Sanity Node public production generation"
emit "Application root: $APP_ROOT"
emit "Configuration: $CONFIG_PATH"
emit "Production output: $OUTPUT_PATH"

emit "Validating production configuration"

if ! run_logged "$VALIDATOR" "$CONFIG_PATH"; then
    fail "configuration validation failed"
fi

runtime_mode="$(
    python3 - "$CONFIG_PATH" <<'PYTHON'
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
PYTHON
)"

if [[ "$runtime_mode" != "public" ]]; then
    fail "production configuration must set dashboard.runtime_mode: public"
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

required_public_markers=(
    "Utility Node Services"
    "T330 Services"
    "T620 Services"
    "public-systems-section"
    "<th>Drive</th>"
)

for marker in "${required_public_markers[@]}"; do
    if ! grep -Fq "$marker" "$temporary_output"; then
        fail "generated dashboard is missing accepted public GUI marker: $marker"
    fi
done

forbidden_public_markers=(
    "<h2>Details</h2>"
    "Runtime Detail"
    "Configured Hosts"
    "Configured Local Storage"
    "<th>Mount</th>"
    "Config Preview"
)

for marker in "${forbidden_public_markers[@]}"; do
    if grep -Fq "$marker" "$temporary_output"; then
        fail "generated public dashboard contains obsolete GUI marker: $marker"
    fi
done

chmod 0664 "$temporary_output"
mv -f -- "$temporary_output" "$OUTPUT_PATH"

output_hash="$(
    sha256sum "$OUTPUT_PATH" |
        awk '{print $1}'
)"

finish_epoch_ns="$(date +%s%N)"

duration_seconds="$(
    LC_ALL=C awk \
        -v start="$start_epoch_ns" \
        -v finish="$finish_epoch_ns" \
        'BEGIN {
            printf "%.3f", (finish - start) / 1000000000
        }'
)"

emit "Public production generation completed successfully"
emit "Output SHA-256: $output_hash"
emit "Runtime seconds: $duration_seconds"

trap - EXIT INT TERM
