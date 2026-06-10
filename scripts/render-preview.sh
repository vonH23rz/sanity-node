#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

CONFIG_FILE="${REPO_ROOT}/examples/config.example.yaml"
GENERATOR="${REPO_ROOT}/scripts/generate-dashboard.py"
OUTPUT_FILE="/tmp/sanity-node-preview.html"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "ERROR: Example configuration not found: ${CONFIG_FILE}" >&2
  exit 1
fi

if [[ ! -f "${GENERATOR}" ]]; then
  echo "ERROR: Dashboard generator not found: ${GENERATOR}" >&2
  exit 1
fi

echo "=== SANITY NODE SAFE PREVIEW RENDER ==="
echo "Configuration: ${CONFIG_FILE}"
echo "Output:        ${OUTPUT_FILE}"
echo

rm -f -- "${OUTPUT_FILE}"

SANITY_NODE_CONFIG="${CONFIG_FILE}" \
SANITY_NODE_OUTPUT="${OUTPUT_FILE}" \
python3 "${GENERATOR}"

if [[ ! -s "${OUTPUT_FILE}" ]]; then
  echo "ERROR: Preview output was not created or is empty." >&2
  exit 1
fi

if ! grep -Fq "host-service-summary-row" "${OUTPUT_FILE}"; then
  echo "ERROR: Host service-card row marker was not found." >&2
  exit 1
fi

if ! grep -Fq "data-host-card=" "${OUTPUT_FILE}"; then
  echo "ERROR: Host service-card marker was not found." >&2
  exit 1
fi

if ! grep -Fq "data-system-row=" "${OUTPUT_FILE}"; then
  echo "ERROR: Public system-row marker was not found." >&2
  exit 1
fi

if grep -Fq "<h2>Details</h2>" "${OUTPUT_FILE}"; then
  echo "ERROR: Public Details heading is still present." >&2
  exit 1
fi

if grep -Fq "Runtime Detail" "${OUTPUT_FILE}"; then
  echo "ERROR: Public Runtime Detail content is still present." >&2
  exit 1
fi

if grep -Fq "Overall Status: OK" "${OUTPUT_FILE}"; then
  if grep -Fq 'data-public-issue-card="true"' "${OUTPUT_FILE}"; then
    echo "ERROR: Healthy public preview unexpectedly contains an issue card." >&2
    exit 1
  fi
else
  if ! grep -Fq 'data-public-issue-card="true"' "${OUTPUT_FILE}"; then
    echo "ERROR: Non-healthy public preview is missing its issue card." >&2
    exit 1
  fi
fi

echo
echo "Preview render passed."
echo "Generated file: ${OUTPUT_FILE}"
