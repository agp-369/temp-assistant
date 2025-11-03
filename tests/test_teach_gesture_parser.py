import pytest
import context
from src.command_parser import parse_command

def test_parse_teach_gesture_simple():
    """Tests parsing a simple 'teach_gesture' command."""
    intent, args = parse_command("teach the thumbs up gesture to next track")
    assert intent == "teach_gesture"
    assert args == {
        "gesture_name": "thumbs_up",
        "command_to_learn": "next track"
    }

def test_parse_teach_gesture_multi_word_command():
    """Tests parsing 'teach_gesture' with a multi-word command."""
    intent, args = parse_command("teach the closed fist gesture to open my work setup")
    assert intent == "teach_gesture"
    assert args == {
        "gesture_name": "closed_fist",
        "command_to_learn": "open my work setup"
    }

def test_parse_teach_gesture_no_the():
    """Tests parsing 'teach_gesture' without the optional 'the'."""
    intent, args = parse_command("teach open palm gesture to lock screen")
    assert intent == "teach_gesture"
    assert args == {
        "gesture_name": "open_palm",
        "command_to_learn": "lock screen"
    }
