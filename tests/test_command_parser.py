import pytest
import context
from src.command_parser import parse_command

def test_parse_open_app():
    """Tests parsing the 'open_app' intent with the new parser."""
    intent, args = parse_command("open notepad")
    assert intent == "open_app"
    assert args == {'app_name': 'notepad'}

    intent, args = parse_command("launch chrome")
    assert intent == "open_app"
    assert args == {'app_name': 'chrome'}

def test_parse_close_app():
    """Tests parsing the 'close_app' intent with the new parser."""
    intent, args = parse_command("close notepad")
    assert intent == "close_app"
    assert args == {'app_name': 'notepad'}

def test_parse_search():
    """Tests parsing the 'search' intent with regex extraction."""
    intent, args = parse_command("search for cat videos")
    assert intent == "search"
    assert args == {"query": "cat videos"}

def test_parse_answer_question():
    """Tests parsing the 'answer_question' intent with regex extraction."""
    intent, args = parse_command("what is the capital of france")
    assert intent == "answer_question"
    assert args == {"query": "the capital of france"}

    intent, args = parse_command("who is albert einstein")
    assert intent == "answer_question"
    assert args == {"query": "albert einstein"}

def test_parse_teach_command():
    """Tests parsing the 'teach_command' intent with regex and split logic."""
    command_str = "teach command work mode to open chrome and then open vscode"
    intent, args = parse_command(command_str)
    assert intent == "teach_command"
    assert args["command_name"] == "work mode"
    assert args["actions"] == ["open chrome", "open vscode"]

def test_parse_play_on_youtube():
    """Tests parsing the 'play_on_youtube' intent with regex extraction."""
    intent, args = parse_command("play epic rock music on youtube")
    assert intent == "play_on_youtube"
    assert args == {"video_title": "epic rock music"}

def test_parse_move_files():
    """Tests parsing a complex 'move_files' intent with multiple entities."""
    command = "move all my pdfs from downloads to documents"
    intent, args = parse_command(command)
    assert intent == "move_files"
    assert args["file_type"] == "all my pdfs"
    assert args["source"] == "downloads"
    assert args["destination"] == "documents"

def test_parse_invalid_command():
    """Tests that invalid commands are not parsed."""
    intent, args = parse_command("this is not a command")
    assert intent is None
    assert not args # args should be an empty dict
