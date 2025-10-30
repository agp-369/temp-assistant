import pytest
import os
import shutil
from unittest.mock import MagicMock
import context
from plugins.file_manager import FileManagerPlugin

@pytest.fixture
def file_manager_setup():
    """Sets up a temporary directory structure for testing file moving."""
    test_dir = "test_file_manager"
    source_dir = os.path.join(test_dir, "downloads")
    dest_dir = os.path.join(test_dir, "documents")
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)

    # Create dummy files
    (open(os.path.join(source_dir, "test1.pdf"), "w")).close()
    (open(os.path.join(source_dir, "test2.pdf"), "w")).close()
    (open(os.path.join(source_dir, "test.txt"), "w")).close()

    yield source_dir, dest_dir

    shutil.rmtree(test_dir)

def test_move_files_confirmation(file_manager_setup):
    """Tests the 'move_files' command, including the confirmation flow."""
    source_dir, dest_dir = file_manager_setup

    # Mock the assistant
    assistant = MagicMock()
    assistant.pending_file_move = None
    assistant.waiting_for_confirmation = False

    plugin = FileManagerPlugin()

    # --- 1. Initial command to find files and ask for confirmation ---
    args = {"file_type": "pdfs", "source": "downloads", "destination": "documents"}

    # This is the critical fix: The plugin uses os.path.expanduser, which we can't
    # easily mock. Instead, we'll patch the plugin's internal `_resolve_folder_path`
    # method to return our temporary test paths.
    def mock_resolve_path(folder_name):
        if folder_name.lower() == "downloads":
            return source_dir
        if folder_name.lower() == "documents":
            return dest_dir
        return None
    plugin._resolve_folder_path = mock_resolve_path

    plugin.move_files(args, assistant)

    # Assert that the assistant is waiting for confirmation
    assistant.speak.assert_called_with("I found 2 files. Are you sure you want to move them from downloads to documents?")
    assert assistant.waiting_for_confirmation is True
    assert assistant.pending_file_move is not None
    assert len(assistant.pending_file_move["files"]) == 2

    # --- 2. Simulate user saying "yes" ---
    # In a real scenario, the assistant's process_command would handle the "yes"
    # and then call execute_file_move. We'll simulate that here.

    # First, capture the pending move from the mock
    pending_move = assistant.pending_file_move

    # Now, we'll manually call the move logic with the captured data
    files_to_move = pending_move["files"]
    dest_path = pending_move["dest"]
    for f in files_to_move:
        shutil.move(f, dest_path)

    # --- 3. Verify files were moved ---
    assert not os.path.exists(os.path.join(source_dir, "test1.pdf"))
    assert not os.path.exists(os.path.join(source_dir, "test2.pdf"))
    assert os.path.exists(os.path.join(dest_dir, "test1.pdf"))
    assert os.path.exists(os.path.join(dest_dir, "test2.pdf"))
    assert os.path.exists(os.path.join(source_dir, "test.txt")) # Should not be moved
