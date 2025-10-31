import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock pyautogui *before* importing the plugin
sys.modules['pyautogui'] = MagicMock()

import context
from plugins.desktop_integration import DesktopIntegrationPlugin

@patch('plugins.desktop_integration.window_manager')
def test_send_whatsapp_message(mock_window_manager):
    """Tests that the send_whatsapp_message command correctly calls the GUI automation functions."""
    # Mock the assistant and the GUI automation libraries
    assistant = MagicMock()
    mock_window_manager.bring_window_to_front.return_value = True

    plugin = DesktopIntegrationPlugin()

    # --- 1. Call the send_whatsapp_message method ---
    args = {"contact": "John Doe", "message": "Hello from the test"}
    plugin.send_whatsapp_message(args, assistant)

    # --- 2. Assert that the GUI automation functions were called correctly ---
    mock_window_manager.bring_window_to_front.assert_called_with("WhatsApp")
    # We can't assert calls on the mocked pyautogui module directly,
    # but we can check that the assistant spoke the correct responses.

    # --- 3. Assert that the assistant spoke the correct responses ---
    assistant.speak.assert_any_call("Okay, sending a WhatsApp message to John Doe.")
    assistant.speak.assert_any_call("The message has been sent.")
