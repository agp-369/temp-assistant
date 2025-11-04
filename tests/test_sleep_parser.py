import pytest
import context
from src.command_parser import parse_command

def test_parse_go_to_sleep():
    """Tests parsing the 'go_to_sleep' intent."""
    intent, args = parse_command("go to sleep")
    assert intent == "go_to_sleep"

    intent, args = parse_command("stop listening")
    assert intent == "go_to_sleep"

    intent, args = parse_command("that's all")
    assert intent == "go_to_sleep"
