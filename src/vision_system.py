import cv2
import threading
import time
import face_recognition
import mediapipe as mp
from . import face_manager

class VisionSystem:
    """
    Manages camera access and processes video frames for features like
    presence detection, face recognition, and gesture control.
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
        self.detected_gesture = None

        self._frame_counter = 0

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

    def learn_current_user_face(self, name):
        # ... (implementation is the same)
        if not self.camera or not self.camera.isOpened(): return "Camera not available."
        success, frame = self.camera.read()
        if not success: return "Failed to capture image."
        face_locations = face_recognition.face_locations(frame)
        if not face_locations: return "No face found."
        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
        self.face_manager.save_face(name, face_encoding)
        self._load_known_faces()
        return f"Learned face for {name}."

    def _load_known_faces(self):
        # ... (implementation is the same)
        known_faces = self.face_manager.get_known_faces()
        self.known_face_names = list(known_faces.keys())
        self.known_face_encodings = list(known_faces.values())
        print(f"Loaded {len(self.known_face_names)} known faces.")

    def start(self):
        # ... (implementation is the same)
        self._load_known_faces()
        if self.is_running: return
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened(): self.camera = None; return
            self.is_running = True
            self.vision_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.vision_thread.start()
            print("Vision system started.")
        except Exception as e:
            print(f"Error initializing camera: {e}"); self.camera = None

    def stop(self):
        # ... (implementation is the same)
        self.is_running = False
        if self.vision_thread: self.vision_thread.join()
        if self.camera: self.camera.release(); self.camera = None
        print("Vision system stopped.")

    def _run_loop(self):
        """The main loop for capturing and processing camera frames."""
        while self.is_running:
            if not self.camera: time.sleep(1); continue
            success, frame = self.camera.read()
            if not success: time.sleep(0.1); continue

            task_index = self._frame_counter % 3
            if task_index == 0:
                self._process_presence(frame)
            elif task_index == 1:
                self._process_recognition(frame)
            else:
                self._process_gestures(frame)

            self._frame_counter += 1
            time.sleep(0.3) # Balance performance

    def _process_presence(self, frame):
        # ... (implementation is the same)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
        if self._last_frame is None: self._last_frame = gray_frame; return
        frame_delta = cv2.absdiff(self._last_frame, gray_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_score = cv2.sumElems(thresh)[0]
        if motion_score > self.motion_threshold:
            self.last_motion_time = time.time()
            self.user_present = True
        if time.time() - self.last_motion_time > self.presence_timeout:
            self.user_present = False
            self.recognized_user = None
        self._last_frame = gray_frame

    def _process_recognition(self, frame):
        # ... (implementation is the same)
        if not self.known_face_encodings: return
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
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
                break
        self.recognized_user = current_recognized_user

    def _process_gestures(self, frame):
        """Analyzes a frame for hand gestures."""
        self.detected_gesture = None # Reset gesture

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # A simple "open palm" gesture detection
                # Check if all key finger tips are above their corresponding PIP joints
                try:
                    thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                    thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
                    index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
                    middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                    middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]

                    if (thumb_tip.x > thumb_ip.x and
                        index_tip.y < index_pip.y and
                        middle_tip.y < middle_pip.y):
                        self.detected_gesture = "open_palm"
                        break # Found gesture, no need to check other hands
                except Exception:
                    pass # Ignore errors if landmarks are not clear
