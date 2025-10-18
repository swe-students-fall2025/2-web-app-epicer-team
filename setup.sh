#!/usr/bin/env bash

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found! Please create one."
  exit 1
fi

set -e  # Exit immediately if a command exits with a non-zero status

echo "Calling virtual environment setup script..."
sudo chmod +x ./demo_scripts/*.sh
./demo_scripts/venv_setup.sh
echo "Virtual environment setup done. Setting up docker demo..."
./demo_scripts/demo_setup.sh
./demo_scripts/demo_start.sh
echo "App setup done"
