import os
import shutil
import glob
from src.plugin_interface import Plugin

class FileManagerPlugin(Plugin):
    """
    A plugin to handle file management commands.
    """
    def get_intent_map(self):
        return {
            "move_files": self.move_files
        }

    def can_handle(self, command):
        return False

    def handle(self, command, assistant):
        pass

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
        return folder_map.get(folder_name.lower())

    def move_files(self, args, assistant):
        """
        Moves files from a source directory to a destination directory.
        """
        file_type = args.get("file_type")
        source = args.get("source")
        destination = args.get("destination")

        if not all([file_type, source, destination]):
            assistant.speak("I'm sorry, I'm missing some information. Please tell me the file type, source, and destination.", is_error=True)
            return

        source_path = self._resolve_folder_path(source)
        dest_path = self._resolve_folder_path(destination)

        if not source_path or not dest_path:
            assistant.speak("I'm sorry, I don't recognize those folder locations.", is_error=True)
            return

        # Find the files
        file_extension = file_type.replace("all my", "").replace("all", "").replace("files", "").strip()
        if file_extension.endswith("s"):
            file_extension = file_extension[:-1]
        if not file_extension.startswith("."):
            file_extension = "." + file_extension

        files_to_move = glob.glob(os.path.join(source_path, f"*{file_extension}"))

        if not files_to_move:
            assistant.speak(f"I couldn't find any {file_extension} files in {source}.")
            return

        # Ask for confirmation
        assistant.speak(f"I found {len(files_to_move)} files. Are you sure you want to move them from {source} to {destination}?")
        assistant.waiting_for_confirmation = True
        assistant.pending_file_move = {"files": files_to_move, "dest": dest_path}
