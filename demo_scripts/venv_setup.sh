#!/usr/bin/env bash
# venv_setup.sh — Create and install virtual environment from requirements.txt

set -e  # Exit immediately if a command exits with a non-zero status

# --- CONFIG ---
PIPENV="pipenv"
PIPENV_CUSTOM_VENV_NAME="dev_env"


# --- CHECK PYTHON ---
if ! command -v "$PYTHON" &>/dev/null; then
  echo "Python not found. Please install Python first."
  exit 1
fi

# --- CREATE VIRTUAL ENVIRONMENT ---
echo "Creating pipenv virtual environment named '$VENV_DIR'..."
export $PIPENV_CUSTOM_VENV_NAME
$PIPENV shell

# --- INSTALL DEPENDENCIES ---
if [ -f Pipfile ]; then
	echo "Installing dependencies from Pipfile"
	$PIPENV install
else
  echo "Pipfile not found! ."
  exit 1
fi

#
echo "Installing dependencies from Pipfile"
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

