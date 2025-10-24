import os
import sys
import json

if sys.platform == "win32":
    import winreg
    from win32com.client import Dispatch

CACHE_FILE = "app_cache.json"

def resolve_shortcut(path):
    """Resolves a .lnk file to its target path."""
    if not path.lower().endswith(".lnk"):
        return path
    try:
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(path)
        return shortcut.TargetPath
    except Exception as e:
        print(f"Error resolving shortcut {path}: {e}")
        return None

def get_installed_apps():
    """
    Scans the system to find installed applications and returns a dictionary
    mapping app names to their executable paths.
    """
    apps = {}

    def search_registry():
        """Scans the Windows Registry for installed applications."""
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for key_path in uninstall_keys:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                if display_name and install_location:
                                    # Look for an executable in the install location
                                    for root, _, files in os.walk(install_location):
                                        for file in files:
                                            if file.lower().endswith(".exe"):
                                                apps[display_name.lower()] = os.path.join(root, file)
                                                break
                                        else:
                                            continue
                                        break
                            except FileNotFoundError:
                                pass
            except FileNotFoundError:
                pass

    def search_start_menu():
        """Scans the Start Menu for application shortcuts."""
        start_menu_paths = [
            os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ["ALLUSERSPROFILE"], r"Microsoft\Windows\Start Menu\Programs")
        ]
        for path in start_menu_paths:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        shortcut_path = os.path.join(root, file)
                        target_path = resolve_shortcut(shortcut_path)
                        if target_path and os.path.isfile(target_path) and target_path.lower().endswith(".exe"):
                            app_name = os.path.splitext(os.path.basename(file))[0]
                            apps[app_name.lower()] = target_path

    if sys.platform == "win32":
        search_registry()
        search_start_menu()

    return apps

def cache_apps():
    """Caches the list of installed applications to a JSON file."""
    apps = get_installed_apps()
    with open(CACHE_FILE, "w") as f:
        json.dump(apps, f, indent=4)
    return apps

def load_cached_apps():
    """Loads the cached list of applications."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return cache_apps()

if __name__ == "__main__":
    print("Discovering applications...")
    discovered_apps = cache_apps()
    print(f"Found {len(discovered_apps)} applications.")
    for name, path in discovered_apps.items():
        print(f"  - {name}: {path}")
