import sys
import psutil

def bring_window_to_front(app_name):
    """Brings the main window of an application to the foreground."""
    if sys.platform != "win32":
        print("Window management is currently only supported on Windows.")
        return False

    try:
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows()
        for window in windows:
            if app_name.lower() in window.window_text().lower():
                window.set_focus()
                return True
    except Exception as e:
        print(f"Error bringing window to front: {e}")

    return False

def close_window(app_name):
    """Closes the main window of an application."""
    if sys.platform != "win32":
        print("Window management is currently only supported on Windows.")
        return False

    try:
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows()
        for window in windows:
            if app_name.lower() in window.window_text().lower():
                window.close()
                return True
    except Exception as e:
        print(f"Error closing window: {e}")

    return False
