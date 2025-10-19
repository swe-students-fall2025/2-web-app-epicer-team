#!/usr/bin/env bash
# setup.sh — Create and install pipenv environment from Pipfile

set -e  # Exit immediately on error

# --- CONFIG ---
PIPENV="pipenv"

# --- CHECK PYTHON ---
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
if ! command -v "$PYTHON" &>/dev/null; then
  echo "Python not found. Please install Python 3 first."
  exit 1
fi

# --- CHECK PIPENV ---
if ! command -v "$PIPENV" &>/dev/null; then
  echo "Pipenv not found. Installing..."
  $PYTHON -m pip install --user pipenv
fi

# --- CREATE / INSTALL ENVIRONMENT ---
echo "Creating Pipenv virtual environment..."
$PIPENV install --dev

# --- ACTIVATE ENVIRONMENT ---
echo "Activating Pipenv shell..."
echo "----------------------------------------"
echo "NOTE: To enter the environment manually later, run:"
echo "    pipenv shell"
echo "----------------------------------------"

exec pipenv shell

# Automatically drop user into pipenv shell if not already in one
if [ -z "${PIPENV_ACTIVE:-}" ]; then
  exec $PIPENV shell
else
  echo "Already inside Pipenv shell."
fi

echo "Pipenv environment setup complete!"