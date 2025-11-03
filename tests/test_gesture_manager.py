import unittest
import os
import json
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gesture_manager import GestureManager

class TestGestureManager(unittest.TestCase):
    def setUp(self):
        self.test_filepath = 'test_gestures.json'

    def tearDown(self):
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)

    def test_load_gestures_file_not_found(self):
        """Tests that an empty dictionary is returned if the file doesn't exist."""
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        manager = GestureManager(filepath=self.test_filepath)
        self.assertEqual(manager.gestures, {})

    def test_load_gestures_file_found(self):
        """Tests that gestures are correctly loaded from an existing file."""
        mock_data = {"thumbs_up": "next track"}
        with open(self.test_filepath, 'w') as f:
            json.dump(mock_data, f)

        manager = GestureManager(filepath=self.test_filepath)
        self.assertEqual(manager.gestures, mock_data)

    def test_save_and_add_gestures(self):
        """Tests adding a new gesture and saving it to the file."""
        manager = GestureManager(filepath=self.test_filepath)

        # Initially empty
        self.assertEqual(manager.gestures, {})

        # Add a gesture
        manager.add_gesture_mapping("thumbs_up", "play music")
        self.assertEqual(manager.gestures, {"thumbs_up": "play music"})

        # Check if it was saved correctly
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, {"thumbs_up": "play music"})

        # Update a gesture
        manager.add_gesture_mapping("thumbs_up", "pause music")
        self.assertEqual(manager.gestures, {"thumbs_up": "pause music"})

        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, {"thumbs_up": "pause music"})


    def test_get_command_for_gesture(self):
        """Tests retrieving a command for a gesture."""
        manager = GestureManager(filepath=self.test_filepath)
        manager.add_gesture_mapping("closed_fist", "stop music")

        command = manager.get_command_for_gesture("closed_fist")
        self.assertEqual(command, "stop music")

        # Test for a gesture that doesn't exist
        command_none = manager.get_command_for_gesture("open_palm")
        self.assertIsNone(command_none)

if __name__ == '__main__':
    unittest.main()
