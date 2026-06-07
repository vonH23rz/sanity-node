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

if ! grep -Fq "Public Four-Card Preview" "${OUTPUT_FILE}"; then
  echo "ERROR: Public four-card preview marker was not found." >&2
  exit 1
fi

if ! grep -Fq "Active cards:" "${OUTPUT_FILE}"; then
  echo "ERROR: Active-card marker was not found." >&2
  exit 1
fi

echo
echo "Preview render passed."
echo "Generated file: ${OUTPUT_FILE}"
