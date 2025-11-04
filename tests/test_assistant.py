import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

import context # Import the context to apply the mock
from src.assistant import Assistant

class TestAssistant(unittest.TestCase):
    def setUp(self):
        with patch.object(Assistant, 'load_config', return_value={'continuous_listen_timeout': 15}) as mock_load_config, \
             patch.object(Assistant, 'load_plugins', return_value=([], {})) as mock_load_plugins:

            self.assistant = Assistant()

        # Mock dependencies that are not relevant to the test
        self.assistant.speak = MagicMock()
        self.assistant.vision = MagicMock() # Already mocked at module level, but good practice

    @patch('src.assistant.parse_command')
    @patch('src.assistant.time.time')
    def test_continuous_listen_loop_timeout(self, mock_time, mock_parse_command):
        """Tests that the continuous listening loop times out correctly."""
        # --- Setup Mocks ---
        # Simulate a sequence of time calls: start, then 20 seconds later
        mock_time.side_effect = [100.0, 120.0]

        # Mock listen_for_command to return None, simulating no user input
        self.assistant.listen_for_command = MagicMock(return_value=None)

        # --- Run the Loop ---
        self.assistant._continuous_listen_loop()

        # --- Assertions ---
        # Check that the timeout message was spoken
        self.assistant.speak.assert_any_call("Timeout reached. Going back to sleep.")
        # Check that the listening state was correctly reset
        self.assertFalse(self.assistant.is_listening)

    @patch('src.assistant.parse_command')
    def test_continuous_listen_loop_go_to_sleep(self, mock_parse_command):
        """Tests that the loop terminates on the 'go_to_sleep' command."""
        # --- Setup Mocks ---
        # Simulate the user saying "go to sleep"
        self.assistant.listen_for_command = MagicMock(return_value="go to sleep")
        mock_parse_command.return_value = ("go_to_sleep", None)

        # --- Run the Loop ---
        self.assistant._continuous_listen_loop()

        # --- Assertions ---
        # Check that the sleep message was spoken
        self.assistant.speak.assert_any_call("Okay, going back to sleep.")
        # Check that the listening state was reset
        self.assertFalse(self.assistant.is_listening)
        # Verify listen_for_command was called (at least once)
        self.assistant.listen_for_command.assert_called()


    @patch('src.assistant.parse_command')
    def test_continuous_listen_loop_multiple_commands(self, mock_parse_command):
        """Tests processing multiple commands before sleeping."""
        # --- Setup Mocks ---
        # Simulate a sequence of user commands
        command_sequence = ["open chrome", "find my report", "go to sleep"]
        self.assistant.listen_for_command = MagicMock(side_effect=command_sequence)

        # Simulate the parser's output for each command
        parse_sequence = [("open_app", "chrome"), ("find_file", "my report"), ("go_to_sleep", None)]
        mock_parse_command.side_effect = parse_sequence

        # Mock the actual process_command method to avoid running the full logic
        self.assistant.process_command = MagicMock()

        # --- Run the Loop ---
        self.assistant._continuous_listen_loop()

        # --- Assertions ---
        # Check that process_command was called for the first two commands
        self.assistant.process_command.assert_any_call("open chrome")
        self.assistant.process_command.assert_any_call("find my report")
        # Ensure it was called exactly twice (not for "go to sleep")
        self.assertEqual(self.assistant.process_command.call_count, 2)

        # Check that the final sleep message was spoken
        self.assistant.speak.assert_any_call("Okay, going back to sleep.")
        # Check that the listening state was reset
        self.assertFalse(self.assistant.is_listening)

if __name__ == '__main__':
    unittest.main()
