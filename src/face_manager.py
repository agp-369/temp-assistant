import pickle
import os

class FaceManager:
    """
    Manages saving and loading known face encodings.
    """
    def __init__(self, data_file="known_faces.dat"):
        self.data_file = data_file
        self.known_faces = self._load_faces()

    def _load_faces(self):
        """Loads face encodings from a file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rb') as f:
                try:
                    return pickle.load(f)
                except EOFError: # File is empty
                    return {}
        return {}

    def save_face(self, name, encoding):
        """Saves a new face encoding."""
        self.known_faces[name] = encoding
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.known_faces, f)

    def get_known_faces(self):
        """Returns the dictionary of known faces and their encodings."""
        return self.known_faces

if __name__ == '__main__':
    # For testing purposes
    fm = FaceManager()
    print("Loaded faces:", fm.get_known_faces().keys())
