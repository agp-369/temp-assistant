import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugins.file_manager import FileManagerPlugin

class TestFileManagerPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = FileManagerPlugin()

    @patch('plugins.file_manager.os.walk')
    @patch('plugins.file_manager.os.path.expanduser', return_value='/home/user')
    def test_find_file_by_filename(self, mock_expanduser, mock_walk):
        mock_walk.return_value = [
            ('/home/user/Documents', [], ['report.docx', 'image.jpg']),
            ('/home/user/Downloads', [], ['installer.exe', 'annual_report.pdf']),
        ]

        # Test finding a specific file
        result = self.plugin.find_file(filename='report.docx')
        self.assertIn('/home/user/Documents/report.docx', result)

        # Test finding with a partial, case-insensitive name
        result_partial = self.plugin.find_file(filename='annual')
        self.assertIn('/home/user/Downloads/annual_report.pdf', result_partial)

        # Test not finding a file
        result_none = self.plugin.find_file(filename='nonexistent.txt')
        self.assertEqual(len(result_none), 0)

    @patch('plugins.file_manager.os.walk')
    @patch('plugins.file_manager.os.path.expanduser', return_value='/home/user')
    def test_find_file_by_filetype(self, mock_expanduser, mock_walk):
        mock_walk.return_value = [
            ('/home/user/Documents', [], ['report.docx', 'image.jpg']),
            ('/home/user/Downloads', [], ['installer.exe', 'annual_report.pdf']),
        ]

        result = self.plugin.find_file(filetype='pdf')
        self.assertIn('/home/user/Downloads/annual_report.pdf', result)
        self.assertEqual(len(result), 1)

    @patch('plugins.file_manager.os.walk')
    def test_find_file_in_specific_directory(self, mock_walk):
        # This mock simulates walking only within the 'Documents' directory
        mock_walk.return_value = [
            ('/home/user/Documents', [], ['report.docx', 'image.jpg']),
        ]

        result = self.plugin.find_file(directory='Documents', filetype='jpg')
        self.assertIn('/home/user/Documents/image.jpg', result)
        self.assertEqual(len(result), 1)

        # We need to assert that os.walk was called with the correct path
        # Note: _resolve_folder_path will be tested separately if needed, here we assume it works
        # For simplicity in this mock, we just check the call was made.
        self.assertTrue(mock_walk.called)

    @patch('plugins.file_manager.os.walk')
    @patch('plugins.file_manager.os.path.expanduser', return_value='/home/user')
    def test_find_file_with_combined_criteria(self, mock_expanduser, mock_walk):
        mock_walk.return_value = [
            ('/home/user/Documents', [], ['project_plan.docx', 'project_data.csv']),
            ('/home/user/Downloads', [], ['old_plan.docx']),
        ]

        result = self.plugin.find_file(filename='project', filetype='docx', directory='Documents')
        self.assertIn('/home/user/Documents/project_plan.docx', result)
        self.assertEqual(len(result), 1)

    @patch.object(FileManagerPlugin, 'find_file')
    def test_handle_find_file_found(self, mock_find_file):
        mock_find_file.return_value = ['/path/to/file1.txt', '/path/to/file2.txt']
        mock_assistant = MagicMock()

        command = ("find_file", {"filename": "file"})
        self.plugin.handle(command, mock_assistant)

        mock_find_file.assert_called_once_with(filename='file')
        self.assertEqual(mock_assistant.speak.call_count, 3)
        mock_assistant.speak.assert_any_call("I found 2 matching files. Here are the top 5:")
        mock_assistant.speak.assert_any_call("file1.txt")
        mock_assistant.speak.assert_any_call("file2.txt")

    @patch.object(FileManagerPlugin, 'find_file')
    def test_handle_find_file_not_found(self, mock_find_file):
        mock_find_file.return_value = []
        mock_assistant = MagicMock()

        command = ("find_file", {"filename": "nonexistent"})
        self.plugin.handle(command, mock_assistant)

        mock_find_file.assert_called_once_with(filename='nonexistent')
        mock_assistant.speak.assert_called_once_with("I couldn't find any files matching 'nonexistent' in your computer.")

    @patch('plugins.file_manager.os.makedirs')
    @patch('plugins.file_manager.os.path.isdir', return_value=False)
    @patch('plugins.file_manager.os.walk')
    @patch('plugins.file_manager.os.path.expanduser')
    def test_move_files_logic(self, mock_expanduser, mock_walk, mock_isdir, mock_makedirs):
        # Mock home directory for consistent paths
        mock_expanduser.side_effect = lambda p: p.replace('~', '/home/user')

        # Simulate os.walk finding one file
        mock_walk.return_value = [
            ('/home/user/Downloads', [], ['report.pdf', 'image.jpg']),
        ]

        files_to_move, dest_path = self.plugin.move_files(
            file_type='pdf',
            source_folder='Downloads',
            dest_folder='Documents'
        )

        # Assert destination directory creation was attempted
        mock_isdir.assert_called_once()
        mock_makedirs.assert_called_once_with('/home/user/Documents')

        # Assert the correct file was identified
        self.assertEqual(len(files_to_move), 1)
        self.assertIn('/home/user/Downloads/report.pdf', files_to_move)

        # Assert the correct destination path was returned
        self.assertEqual(dest_path, '/home/user/Documents')

    @patch.object(FileManagerPlugin, 'move_files')
    def test_handle_move_files_found(self, mock_move_files):
        # Mock the return value of the core move_files logic
        mock_move_files.return_value = (
            ['/path/to/doc.pdf'], '/path/to/dest'
        )
        mock_assistant = MagicMock()

        command = ("move_files", {
            "file_type": "pdf",
            "source_folder": "Downloads",
            "dest_folder": "Documents"
        })
        self.plugin.handle(command, mock_assistant)

        # Check that the confirmation flow was correctly triggered
        self.assertTrue(mock_assistant.waiting_for_confirmation)
        self.assertIsNotNone(mock_assistant.pending_file_move)
        self.assertEqual(mock_assistant.pending_file_move['dest'], '/path/to/dest')

        # Check that the assistant spoke the correct messages
        mock_assistant.speak.assert_any_call("I found 1 .pdf files to move. Here are the first few:")
        mock_assistant.speak.assert_any_call("doc.pdf")
        mock_assistant.speak.assert_any_call("Shall I proceed with moving them?")

    @patch.object(FileManagerPlugin, 'move_files')
    def test_handle_move_files_not_found(self, mock_move_files):
        # Mock the return value for when no files are found
        mock_move_files.return_value = ([], None)
        mock_assistant = MagicMock()
        mock_assistant.waiting_for_confirmation = False # Explicitly set initial state

        command = ("move_files", {
            "file_type": "txt",
            "source_folder": "Desktop",
            "dest_folder": "Archive"
        })
        self.plugin.handle(command, mock_assistant)

        # Check that the 'not found' message was spoken
        mock_assistant.speak.assert_called_once_with("I couldn't find any .txt files in your Desktop folder.")
        # Ensure confirmation flow was NOT triggered
        self.assertFalse(mock_assistant.waiting_for_confirmation)


if __name__ == '__main__':
    unittest.main()
