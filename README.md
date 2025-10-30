# Desktop-Assistant

An advanced, smart desktop AI assistant that can work both offline and online.

## Installation Options

This project offers two installation paths.

### 1. Core Installation (Recommended for a quick start)

This method installs only the essential dependencies for the assistant's core features, such as command processing, web interaction, and file management. It is faster and avoids the complex installation of large AI/ML libraries.

1.  **Install system dependencies:**
    *   On Debian/Ubuntu, run:
        ```bash
        sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio scrot python3-tk python3-dev
        ```
2.  **Install core Python packages:**
    ```bash
    pip install -r requirements-core.txt
    ```

### 2. Full Installation (Enables all features)

This method installs all dependencies, including the heavy computer vision and AI libraries that power the advanced features.

**Prerequisites:**
*   A C++ compiler (e.g., GCC, MSVC)
*   CMake (`pip install cmake`)

**Installation:**
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```
**Note:** This script can take a long time to run, as it compiles large libraries like `dlib` from source.

## Graceful Feature Degradation

The application is designed to be resilient. If you perform a core installation, the advanced vision and memory features will be automatically disabled, but the rest of the assistant will remain fully functional. You will see warning messages in the console indicating which features have been disabled.

## Running the Application
```bash
python main.py
```

## Vision Features

To enable the face recognition features, you must install the vision dependencies:
```bash
pip install -r requirements-vision.txt
```
**Note:** This may take a long time and requires a C++ compiler and CMake.

### Available Vision Commands
*   `learn my face as [your name]`: Teaches the assistant to recognize your face.
*   `who am I`: The assistant will respond with the name of the recognized user.
