import sys
import time

def get_active_window_info():
    """
    Gets information about the currently active window.
    Returns a dictionary with the window title and process name.
    """
    if sys.platform != "win32":
        return None

    try:
        from pywinauto import Desktop
        import psutil

        windows = Desktop(backend="uia").windows()
        for w in windows:
            if w.is_active():
                process_name = psutil.Process(w.process_id()).name()
                return {
                    "title": w.window_text(),
                    "process_name": process_name
                }
    except Exception as e:
        print(f"Error getting active window info: {e}")

    return None

def get_browser_url(process_name):
    """
    Gets the URL from the active tab of a web browser.
    Supports Chrome, Firefox, and Edge.
    """
    if sys.platform != "win32" or process_name.lower() not in ["chrome.exe", "firefox.exe", "msedge.exe"]:
        return None

    try:
        from pywinauto import Desktop

        app = Desktop(backend="uia").child_window(process_name=process_name, top_level_only=True)
        url = app.child_window(control_type="Edit", top_level_only=False).get_value()
        return url
    except Exception as e:
        print(f"Error getting browser URL: {e}")
        return None

if __name__ == "__main__":
    while True:
        info = get_active_window_info()
        if info:
            print(f"Active Window: '{info['title']}' from process '{info['process_name']}'")
        time.sleep(2)
