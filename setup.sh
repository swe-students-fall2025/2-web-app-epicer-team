
#!/usr/bin/env bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Calling virtual environment setup script..."
sudo chmod +x ./demo_scripts/*.sh
./demo_scripts/venv_setup.sh
echo "Virtual environment setup done. Setting up docker demo..."
./demo_scripts/demo_setup.sh
./demo_scripts/demo_start.sh
echo "App setup done"
