#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/../backend" && pwd)"
ENV_DIR="${BACKEND_DIR}/.venv"

echo "Backend project: ${BACKEND_DIR}"
echo "Target environment: ${ENV_DIR}"

echo "Syncing project dependencies via uv..."
uv sync --project "${BACKEND_DIR}"

echo "Environment setup complete. Run 'source ${ENV_DIR}/bin/activate' before development."
