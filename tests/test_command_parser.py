import pytest
import context
from src.command_parser import parse_command

def test_parse_open_app():
    """Tests parsing the 'open_app' intent."""
    intent, args = parse_command("open notepad")
    assert intent == "open_app"
    assert args == "notepad"

    intent, args = parse_command("launch chrome")
    assert intent == "open_app"
    assert args == "chrome"

def test_parse_close_app():
    """Tests parsing the 'close_app' intent."""
    intent, args = parse_command("close notepad")
    assert intent == "close_app"
    assert args == "notepad"

def test_parse_search():
    """Tests parsing the 'search' intent."""
    intent, args = parse_command("search for cat videos")
    assert intent == "search"
    assert args == "cat videos"

def test_parse_answer_question():
    """Tests parsing the 'answer_question' intent."""
    intent, args = parse_command("what is the capital of france")
    assert intent == "answer_question"
    assert args == "the capital of france"

    intent, args = parse_command("who is albert einstein")
    assert intent == "answer_question"
    assert args == "albert einstein"

def test_parse_teach_command():
    """Tests parsing the 'teach_command' intent."""
    command_str = "teach command work mode to open chrome and then open vscode"
    intent, args = parse_command(command_str)
    command_name, actions = args
    assert intent == "teach_command"
    assert command_name == "work mode"
    assert actions == ["open chrome", "open vscode"]

def test_parse_invalid_command():
    """Tests that invalid commands are not parsed."""
    intent, args = parse_command("this is not a command")
    assert intent is None
    assert args is None
