#!/bin/bash
# This script installs the dependencies for the desktop assistant.

# For Linux users, PyAudio and pyautogui require some additional system packages.
# The following commands should work for Debian-based systems (like Ubuntu).
# If you are on a different Linux distribution, you may need to use a different package manager.
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux. Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio scrot python3-tk python3-dev tesseract-ocr
fi

# Now, install the Python dependencies.
pip install -r requirements.txt
