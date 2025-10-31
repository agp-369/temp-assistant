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

    def move_files(self, assistant, file_type, source_folder, dest_folder):
        """Moves files of a certain type from a source to a destination."""
        source_path = self._resolve_folder_path(source_folder)
        dest_path = self._resolve_folder_path(dest_folder)

        if not os.path.isdir(dest_path):
            os.makedirs(dest_path) # Create destination if it doesn't exist

        pattern = f"*.{file_type.lower()}"
        files_to_move = glob.glob(os.path.join(source_path, pattern))

        if not files_to_move:
            assistant.speak(f"I couldn't find any .{file_type} files in your {source_folder} folder.")
            return []

        # Return the list of files for the confirmation step
        return files_to_move


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
            # Example args: "PDFs from Downloads to Documents"
            parts = args.split(" from ")
            file_type = parts[0].replace("s", "") # Handle plurals like "PDFs"
            source_dest = parts[1].split(" to ")
            source = source_dest[0]
            dest = source_dest[1]

            files = self.move_files(assistant, file_type, source, dest)
            if files:
                # This is where the confirmation flow will be triggered
                assistant.pending_file_move = {
                    "files": files,
                    "dest": self._resolve_folder_path(dest)
                }
                assistant.speak(f"I found {len(files)} .{file_type} files to move. Here are the first few:")
                for f in files[:3]:
                    assistant.speak(os.path.basename(f))
                assistant.speak("Shall I proceed with moving them?")
                assistant.waiting_for_confirmation = True
