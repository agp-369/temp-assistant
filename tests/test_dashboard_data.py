import pytest
from unittest.mock import patch
import context
from src import dashboard_data

@patch('src.dashboard_data.psutil.process_iter')
def test_get_running_applications(mock_process_iter):
    """Tests that the running applications list is correctly filtered."""
    # Mock the process list returned by psutil
    mock_process_iter.return_value = [
        # A mock process object
        type('Process', (object,), {
            'info': {'name': 'chrome.exe', 'username': 'testuser'}
        }),
        type('Process', (object,), {
            'info': {'name': 'svchost.exe', 'username': 'SYSTEM'} # Should be filtered
        }),
        type('Process', (object,), {
            'info': {'name': 'explorer.exe', 'username': 'testuser'}
        }),
    ]

    apps = dashboard_data.get_running_applications()
    assert "chrome.exe" in apps
    assert "explorer.exe" in apps
    assert "svchost.exe" not in apps

@patch('src.dashboard_data.usage_tracker.load_stats')
def test_get_recent_files(mock_load_stats):
    """Tests that recent files are correctly sorted by usage."""
    mock_load_stats.return_value = {
        "files": {
            "report.docx": 10,
            "notes.txt": 5,
            "presentation.pptx": 15
        }
    }

    files = dashboard_data.get_recent_files()
    assert files == ["presentation.pptx", "report.docx", "notes.txt"]

@patch('src.dashboard_data.custom_commands.load_commands')
def test_get_custom_shortcuts(mock_load_commands):
    """Tests that custom command names are retrieved correctly."""
    mock_load_commands.return_value = {
        "work mode": ["open chrome", "open vscode"],
        "relax": ["play music"]
    }

    shortcuts = dashboard_data.get_custom_shortcuts()
    assert shortcuts == ["relax", "work mode"]
