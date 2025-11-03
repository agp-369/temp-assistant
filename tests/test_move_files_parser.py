import pytest
import context
from src.command_parser import parse_command

def test_parse_move_files_simple():
    """Tests parsing a simple 'move_files' command."""
    intent, args = parse_command("move pdfs from downloads to documents")
    assert intent == "move_files"
    assert args == {
        "file_type": "pdf",
        "source_folder": "downloads",
        "dest_folder": "documents"
    }

def test_parse_move_files_with_all():
    """Tests parsing 'move_files' with the 'all' keyword."""
    intent, args = parse_command("move all png files from desktop to pictures")
    assert intent == "move_files"
    assert args == {
        "file_type": "png",
        "source_folder": "desktop",
        "dest_folder": "pictures"
    }

def test_parse_move_files_multi_word_folders():
    """Tests parsing 'move_files' with multi-word folder names."""
    intent, args = parse_command("move txt files from my project folder to the archive folder")
    assert intent == "move_files"
    assert args == {
        "file_type": "txt",
        "source_folder": "my project folder",
        "dest_folder": "the archive folder"
    }
