import json
import os

COMMANDS_FILE = "custom_commands.json"

def load_commands():
    """
    Loads custom commands from the JSON file.
    Returns a dictionary of commands.
    """
    if not os.path.exists(COMMANDS_FILE):
        return {}
    try:
        with open(COMMANDS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_command(name, actions):
    """
    Saves a new custom command.

    Args:
        name (str): The name of the command (the phrase to trigger it).
        actions (list): A list of action strings to be executed.
    """
    commands = load_commands()
    commands[name.lower()] = actions
    try:
        with open(COMMANDS_FILE, "w") as f:
            json.dump(commands, f, indent=4)
        return True
    except IOError:
        return False
