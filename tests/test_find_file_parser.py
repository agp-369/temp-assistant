import pytest
import context
from src.command_parser import parse_command

def test_parse_find_file_by_name():
    """Tests parsing 'find_file' with a specific filename."""
    intent, args = parse_command("find my_document.txt")
    assert intent == "find_file"
    assert args == {"filename": "my_document.txt", "filetype": None, "directory": None}

def test_parse_find_file_by_name_no_extension():
    """Tests parsing 'find_file' with a filename without an extension."""
    intent, args = parse_command("find quarterly report")
    assert intent == "find_file"
    assert args == {"filename": "quarterly report", "filetype": None, "directory": None}

def test_parse_find_file_by_type():
    """Tests parsing 'find_file' with a file type."""
    intent, args = parse_command("locate all pdf files")
    assert intent == "find_file"
    assert args == {"filename": None, "filetype": "pdf", "directory": None}

def test_parse_find_file_by_name_in_directory():
    """Tests parsing 'find_file' with a name and a directory."""
    intent, args = parse_command("find presentation in Documents")
    assert intent == "find_file"
    assert args == {"filename": "presentation", "filetype": None, "directory": "Documents"}

def test_parse_find_file_by_type_in_directory():
    """Tests parsing 'find_file' with a file type and a directory."""
    intent, args = parse_command("find docx files in Downloads")
    assert intent == "find_file"
    assert args == {"filename": None, "filetype": "docx", "directory": "Downloads"}

def test_parse_find_file_complex_name_in_directory():
    """Tests parsing 'find_file' with a multi-word name and a directory."""
    intent, args = parse_command("find the annual financial report in my Shared Drive")
    assert intent == "find_file"
    assert args == {"filename": "annual financial report", "filetype": None, "directory": "my Shared Drive"}
