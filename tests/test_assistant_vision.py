import pytest
from unittest.mock import MagicMock
import context
from src.assistant import Assistant

def test_who_are_you_recognized():
    """Tests the 'who_are_you' command when a user is recognized."""
    # Create a mock assistant object
    assistant = MagicMock()
    assistant.vision = MagicMock()
    assistant.vision.recognized_user = "Jules"

    # We need to attach the real who_are_you method to the mock
    assistant.who_are_you = Assistant.who_are_you.__get__(assistant)

    # Call the method to be tested
    assistant.who_are_you()

    # Assert that the assistant spoke the correct response
    assistant.speak.assert_called_with("I see you, Jules.")

def test_who_are_you_unrecognized():
    """Tests the 'who_are_you' command when a user is not recognized."""
    # Create a mock assistant object
    assistant = MagicMock()
    assistant.vision = MagicMock()
    assistant.vision.recognized_user = None

    # We need to attach the real who_are_you method to the mock
    assistant.who_are_you = Assistant.who_are_you.__get__(assistant)

    # Call the method to be tested
    assistant.who_are_you()

    # Assert that the assistant spoke the correct response
    assistant.speak.assert_called_with("I don't recognize you. You can teach me to recognize you by saying 'learn my face as [your name]'.")
