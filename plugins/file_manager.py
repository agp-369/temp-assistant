from src.plugin_interface import Plugin
import os
import shutil
import glob

class FileManagerPlugin(Plugin):
    """
    A plugin to handle advanced file management commands like finding and moving files.
    """
    def get_intent_map(self):
        return {
            "find_file": self.handle,
            "move_files": self.handle
        }

    def can_handle(self, command):
        return False # This plugin is intent-based

    def _resolve_folder_path(self, folder_name):
        """Resolves common folder names to their full paths."""
        home = os.path.expanduser("~")
        folder_map = {
            "downloads": os.path.join(home, "Downloads"),
            "documents": os.path.join(home, "Documents"),
            "desktop": os.path.join(home, "Desktop"),
            "pictures": os.path.join(home, "Pictures"),
            "music": os.path.join(home, "Music"),
            "videos": os.path.join(home, "Videos"),
        }
        return folder_map.get(folder_name.lower(), home) # Default to home dir

    def find_file(self, filename=None, filetype=None, directory=None):
        """
        Finds files based on filename, filetype, and/or directory.

        Args:
            filename (str, optional): The name of the file to search for.
            filetype (str, optional): The extension of the files to search for (e.g., 'pdf').
            directory (str, optional): The directory to search in. Defaults to the user's home directory.

        Returns:
            list: A list of paths to the found files.
        """
        search_path = self._resolve_folder_path(directory) if directory else os.path.expanduser("~")

        found_files = []

        for root, dirs, files in os.walk(search_path):
            for file in files:
                # Filter by filetype if provided
                if filetype and not file.lower().endswith(f".{filetype}"):
                    continue

                # Filter by filename if provided (case-insensitive)
                if filename and filename.lower() not in file.lower():
                    continue

                found_files.append(os.path.join(root, file))

        return found_files

    def move_files(self, file_type, source_folder, dest_folder):
        """
        Finds all files of a specific type in a source folder, ready for moving.

        Returns:
            A tuple containing (list_of_files_to_move, destination_path).
            Returns ([], None) if no files are found.
        """
        source_path = self._resolve_folder_path(source_folder)
        dest_path = self._resolve_folder_path(dest_folder)

        if not os.path.isdir(dest_path):
            try:
                os.makedirs(dest_path)
            except OSError as e:
                # Handle potential race condition or permission errors
                return [], None

        files_to_move = []
        for root, _, files in os.walk(source_path):
            for file in files:
                if file.lower().endswith(f".{file_type.lower()}"):
                    files_to_move.append(os.path.join(root, file))

        return files_to_move, dest_path


    def handle(self, command, assistant):
        intent, args = command

        if intent == "find_file":
            files = self.find_file(**args)

            if not files:
                search_term = args.get('filename') or args.get('filetype')
                directory = args.get('directory', 'your computer')
                assistant.speak(f"I couldn't find any files matching '{search_term}' in {directory}.")
            else:
                assistant.speak(f"I found {len(files)} matching files. Here are the top 5:")
                for f in files[:5]:
                    assistant.speak(os.path.basename(f))

        elif intent == "move_files":
            files_to_move, dest_path = self.move_files(**args)

            if not files_to_move:
                assistant.speak(f"I couldn't find any .{args['file_type']} files in your {args['source_folder']} folder.")
                return

            if dest_path:
                assistant.pending_file_move = {
                    "files": files_to_move,
                    "dest": dest_path
                }
                assistant.speak(f"I found {len(files_to_move)} .{args['file_type']} files to move. Here are the first few:")
                for f in files_to_move[:3]:
                    assistant.speak(os.path.basename(f))
                assistant.speak("Shall I proceed with moving them?")
                assistant.waiting_for_confirmation = True
