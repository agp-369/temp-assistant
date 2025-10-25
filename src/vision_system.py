import cv2
import threading
import time
import face_recognition
from . import face_manager

class VisionSystem:
    """
    Manages camera access and processes video frames for features like
    presence detection, face recognition, etc.
    """
    def __init__(self, motion_threshold=500000, presence_timeout=5.0):
        self.is_running = False
        self.camera = None
        self.vision_thread = None

        self.user_present = False
        self.last_motion_time = 0
        self.motion_threshold = motion_threshold
        self.presence_timeout = presence_timeout

        self._last_frame = None
        self.face_manager = face_manager.FaceManager()
        self.known_face_encodings = []
        self.known_face_names = []
        self.recognized_user = None

        # Counter to process different tasks on different frames for performance
        self._frame_counter = 0

    def learn_current_user_face(self, name):
        """Captures the current user's face and saves the encoding."""
        if not self.camera or not self.camera.isOpened():
            return "Camera is not available."

        success, frame = self.camera.read()
        if not success:
            return "Failed to capture an image from the camera."

        face_locations = face_recognition.face_locations(frame)
        if not face_locations:
            return "I couldn't see a face in the camera. Please look at the camera and try again."

        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

        self.face_manager.save_face(name, face_encoding)
        self._load_known_faces()
        return f"I've learned your face as {name}."

    def _load_known_faces(self):
        """Loads known faces from the FaceManager."""
        known_faces = self.face_manager.get_known_faces()
        self.known_face_names = list(known_faces.keys())
        self.known_face_encodings = list(known_faces.values())
        print(f"Loaded {len(self.known_face_names)} known faces.")

    def start(self):
        """Initializes the camera and starts the vision processing thread."""
        self._load_known_faces()
        if self.is_running:
            print("Vision system is already running.")
            return

        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("Error: Could not open camera.")
                self.camera = None
                return

            self.is_running = True
            self.vision_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.vision_thread.start()
            print("Vision system started.")

        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None

    def stop(self):
        """Stops the vision processing thread and releases the camera."""
        self.is_running = False
        if self.vision_thread:
            self.vision_thread.join()
        if self.camera:
            self.camera.release()
            self.camera = None
        print("Vision system stopped.")

    def _run_loop(self):
        """The main loop for capturing and processing camera frames."""
        while self.is_running:
            if not self.camera:
                time.sleep(1)
                continue

            success, frame = self.camera.read()
            if not success:
                time.sleep(0.1)
                continue

            self._frame_counter += 1

            # Process presence detection on even frames
            if self._frame_counter % 2 == 0:
                self._process_presence(frame)
            # Process face recognition on odd frames
            else:
                self._process_recognition(frame)

            time.sleep(0.5) # Balance performance and responsiveness

    def _process_presence(self, frame):
        """Analyzes a frame for motion to detect user presence."""
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        if self._last_frame is None:
            self._last_frame = gray_frame
            return

        frame_delta = cv2.absdiff(self._last_frame, gray_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_score = cv2.sumElems(thresh)[0]

        if motion_score > self.motion_threshold:
            self.last_motion_time = time.time()
            self.user_present = True

        if time.time() - self.last_motion_time > self.presence_timeout:
            self.user_present = False
            self.recognized_user = None # Reset recognized user when absent

        self._last_frame = gray_frame

    def _process_recognition(self, frame):
        """Analyzes a frame for faces and attempts to recognize them."""
        if not self.known_face_encodings:
            return

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        # Convert the image from BGR color (which OpenCV uses) to RGB color
        rgb_small_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        current_recognized_user = None
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)

            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]
                current_recognized_user = name
                break # Recognize the first match

        self.recognized_user = current_recognized_user

if __name__ == '__main__':
    vision = VisionSystem()
    vision.start()

    # Simulate learning a face after a few seconds
    # In a real scenario, this would be triggered by a command.

    try:
        print("Monitoring... Press Ctrl+C to stop.")
        while True:
            status = "Present" if vision.user_present else "Absent"
            user = vision.recognized_user or "Unknown"
            print(f"Status: {status}, User: {user}", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        vision.stop()
