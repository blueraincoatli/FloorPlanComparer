#!/usr/bin/env bash
set -euo pipefail

ENV_PATH=${1:-.venv}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_DIR="${PROJECT_ROOT}/${ENV_PATH}"

echo "Project root: ${PROJECT_ROOT}"
echo "Virtual environment: ${ENV_DIR}"

if [[ ! -d "${ENV_DIR}" ]]; then
  echo "Creating virtual environment via uv..."
  uv venv "${ENV_DIR}"
else
  echo "Virtual environment already exists."
fi

PYTHON_BIN="${ENV_DIR}/bin/python"

echo "Installing Poetry into the uv-managed environment..."
uv pip install --python "${PYTHON_BIN}" poetry

echo "Activating environment and installing backend dependencies..."
export POETRY_VIRTUALENVS_CREATE=false
export POETRY_VIRTUALENVS_IN_PROJECT=false
# shellcheck disable=SC1090
source "${ENV_DIR}/bin/activate"

pushd "${PROJECT_ROOT}/backend" >/dev/null
poetry install --no-interaction --no-root
popd >/dev/null

echo "Environment setup complete. Run 'source ${ENV_DIR}/bin/activate' before development."
