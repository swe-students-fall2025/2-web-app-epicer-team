#!/usr/bin/env bash
# venv_setup.sh — Create and install virtual environment from requirements.txt

set -e  # Exit immediately if a command exits with a non-zero status

# --- CONFIG ---
PYTHON=${PYTHON:-python3}
VENV_DIR="dev_env"
REQ_FILE=${REQ_FILE:-requirements.txt}

# --- CHECK PYTHON ---
if ! command -v "$PYTHON" &>/dev/null; then
  echo "Python not found. Please install Python 3 first."
  exit 1
fi

# --- CREATE VIRTUAL ENVIRONMENT ---
echo "Creating virtual environment in '$VENV_DIR'..."
$PYTHON -m venv "$VENV_DIR"

# --- ACTIVATE VENV ---
# shellcheck disable=SC1091
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ "$OSTYPE" == "msys"* ]]; then
  source "$VENV_DIR/bin/activate"
else
  source "$VENV_DIR/Scripts/activate"
fi

# --- UPGRADE PIP ---
echo "Upgrading pip..."
pip install --upgrade pip

# --- INSTALL DEPENDENCIES ---
if [ -f "$REQ_FILE" ]; then
  echo "Installing dependencies from $REQ_FILE..."
  pip install -r "$REQ_FILE"
else
  echo "No requirements.txt found. Skipping dependency installation. Please check for requirements.txt in current directory"
fi

echo "Virtual environment setup complete!"

