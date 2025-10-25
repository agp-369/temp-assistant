import psutil
from . import usage_tracker
from . import custom_commands

def get_running_applications():
    """
    Scans for running processes and returns a list of likely user applications.
    """
    apps = []
    for proc in psutil.process_iter(['name', 'username']):
        try:
            # This is a simple heuristic: filter by username and common process names
            # that are likely GUI applications. This can be improved.
            if proc.info['username'] is not None and proc.info['name'].endswith('.exe'):
                # Avoid some common background/system processes
                if proc.info['name'] not in ['svchost.exe', 'conhost.exe', 'runtimebroker.exe']:
                    apps.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # Return a unique list
    return sorted(list(set(apps)))

def get_recent_files():
    """
    Retrieves a list of recently used files from the usage tracker.
    Returns a list of filenames sorted by usage count.
    """
    stats = usage_tracker.load_stats()
    files = stats.get("files", {})
    # Sort files by usage count, descending
    sorted_files = sorted(files.items(), key=lambda item: item[1], reverse=True)
    return [file for file, count in sorted_files]

def get_custom_shortcuts():
    """
    Retrieves the names of all taught custom commands.
    """
    commands = custom_commands.load_commands()
    return sorted(list(commands.keys()))

if __name__ == '__main__':
    print("--- Running Applications ---")
    running_apps = get_running_applications()
    for app in running_apps[:10]: # Print top 10 for brevity
        print(f"  - {app}")

    print("\n--- Recent Files ---")
    recent_files = get_recent_files()
    for file in recent_files[:10]:
        print(f"  - {file}")

    print("\n--- Custom Shortcuts ---")
    shortcuts = get_custom_shortcuts()
    for shortcut in shortcuts:
        print(f"  - {shortcut}")
