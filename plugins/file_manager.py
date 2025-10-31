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
            "find_files": self.handle,
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

    def find_files(self, assistant, file_type=None, folder=None):
        """Finds files based on type and/or folder."""
        search_path = self._resolve_folder_path(folder) if folder else os.path.expanduser("~")

        pattern = f"**/*.{file_type.lower() if file_type else '*'}"
        files = glob.glob(os.path.join(search_path, pattern), recursive=True)

        if not files:
            assistant.speak(f"I couldn't find any {file_type} files in {folder if folder else 'your home directory'}.")
        else:
            assistant.speak(f"I found {len(files)} {file_type or ''} files. Here are the first 5:")
            for f in files[:5]:
                assistant.speak(os.path.basename(f))

        return files

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

        if intent == "find_files":
            # Example args: "PDF in Downloads"
            parts = args.split(" in ")
            file_type = parts[0]
            folder = parts[1] if len(parts) > 1 else None
            self.find_files(assistant, file_type=file_type, folder=folder)

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
