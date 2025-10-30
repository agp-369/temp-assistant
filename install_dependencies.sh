#!/bin/bash
# A robust installation script for the Desktop Assistant.

set -e # Exit immediately if a command exits with a non-zero status.

# --- 1. System-Level Dependencies ---
echo "INFO: Installing system-level dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio scrot python3-tk python3-dev tesseract-ocr cmake build-essential
else
    echo "WARNING: Skipping system dependency installation. This script is configured for Debian-based Linux."
fi
echo "INFO: System dependencies installation complete."
echo "--------------------------------------------------"

# --- 2. Python Dependencies ---
echo "INFO: Installing core Python packages..."
pip install --no-cache-dir -r requirements-core.txt

echo "INFO: Installing vision Python packages..."
pip install --no-cache-dir -r requirements-vision.txt

echo "INFO: Installing all remaining Python packages..."
pip install --no-cache-dir -r requirements.txt

echo "INFO: All dependencies have been installed successfully!"
