import json
import os

STATS_FILE = "usage_stats.json"

def load_stats():
    """
    Loads usage statistics from the JSON file.
    """
    if not os.path.exists(STATS_FILE):
        return {"apps": {}, "files": {}}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"apps": {}, "files": {}}

def save_stats(stats):
    """
    Saves the usage statistics to the JSON file.
    """
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
    except IOError:
        pass

def track_app_usage(app_name):
    """
    Increments the usage count for a given application.
    """
    stats = load_stats()
    app_name_lower = app_name.lower()
    stats["apps"][app_name_lower] = stats["apps"].get(app_name_lower, 0) + 1
    save_stats(stats)

def track_file_usage(filename):
    """
    Increments the usage count for a given file.
    """
    stats = load_stats()
    filename_lower = filename.lower()
    stats["files"][filename_lower] = stats["files"].get(filename_lower, 0) + 1
    save_stats(stats)
