import json
import os

class GestureManager:
    """
    Manages the loading and saving of custom gesture-to-command mappings.
    """
    def __init__(self, filepath='custom_gestures.json'):
        self.filepath = filepath
        self.gestures = self.load_gestures()

    def load_gestures(self):
        """Loads gesture mappings from the JSON file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {}

    def save_gestures(self):
        """Saves the current gesture mappings to the JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(self.gestures, f, indent=4)

    def add_gesture_mapping(self, gesture, command):
        """
        Adds or updates a mapping for a gesture to a command.

        Args:
            gesture (str): The name of the gesture (e.g., 'thumbs_up').
            command (str): The command string to execute.
        """
        self.gestures[gesture] = command
        self.save_gestures()

    def get_command_for_gesture(self, gesture):
        """
        Retrieves the command associated with a given gesture.

        Args:
            gesture (str): The name of the gesture.

        Returns:
            str: The command string, or None if no mapping exists.
        """
        return self.gestures.get(gesture)
