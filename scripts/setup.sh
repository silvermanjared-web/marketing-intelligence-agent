#!/usr/bin/env bash
#
# Setup script for Marketing Intelligence Agent
# Creates a virtual environment and installs dependencies.
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/venv"

echo ""
echo "  Marketing Intelligence Agent — Setup"
echo "  ====================================="
echo ""

# Create virtual environment if it doesn't exist.
if [ ! -d "${VENV_DIR}" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"
    echo "  [OK] Virtual environment created at ${VENV_DIR}"
else
    echo "  [OK] Virtual environment already exists"
fi

# Activate and install dependencies.
echo "  Installing dependencies..."
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "${REPO_ROOT}/requirements.txt"
echo "  [OK] Dependencies installed"

# Create config files from examples if they don't exist.
CONFIG_DIR="${REPO_ROOT}/config"

if [ ! -f "${CONFIG_DIR}/projects.json" ]; then
    cp "${CONFIG_DIR}/projects.example.json" "${CONFIG_DIR}/projects.json"
    echo "  [OK] Created config/projects.json from example — edit with your project paths"
else
    echo "  [OK] config/projects.json already exists"
fi

if [ ! -f "${CONFIG_DIR}/modes.json" ]; then
    cp "${CONFIG_DIR}/modes.example.json" "${CONFIG_DIR}/modes.json"
    echo "  [OK] Created config/modes.json from example"
else
    echo "  [OK] config/modes.json already exists"
fi

# Create logs directory.
mkdir -p "${REPO_ROOT}/logs"

echo ""
echo "  Setup complete. To get started:"
echo ""
echo "    source venv/bin/activate"
echo "    python hub.py"
echo ""
