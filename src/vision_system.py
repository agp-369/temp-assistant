import threading
import time
from . import face_manager

# --- Graceful Vision Imports ---
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV (cv2) not found. Vision system will be disabled.")

try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("Warning: face_recognition not found. Face recognition features will be disabled.")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not found. Gesture detection will be disabled.")

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: deepface not found. Emotion detection will be disabled.")

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract not found. OCR features will be disabled.")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics (YOLO) not found. Object detection will be disabled.")
# --- End Graceful Imports ---


class VisionSystem:
    """
    Manages camera access and processes video frames for various AI tasks.
    Features are gracefully disabled if dependencies are not met.
    """
    def __init__(self, motion_threshold=500000, presence_timeout=5.0):
        # ... (init attributes are the same)
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
        self.detected_emotion = None
        self.detected_objects = []
        self._frame_counter = 0

        # Conditionally initialize vision components
        if not CV2_AVAILABLE:
            print("VisionSystem disabled due to missing OpenCV.")
            return

        self.mp_hands = None
        self.hands = None
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
            self.mp_draw = mp.solutions.drawing_utils

        self.yolo_model = None
        if YOLO_AVAILABLE:
            try:
                self.yolo_model = YOLO("yolov8n.pt")
            except Exception as e:
                print(f"Warning: Failed to load YOLO model. Object detection disabled. Error: {e}")
                self.yolo_model = None

    def learn_current_user_face(self, name):
        # ... (implementation is the same)
        if not FACE_REC_AVAILABLE:
            return "Face recognition is disabled due to missing libraries."
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
        if not CV2_AVAILABLE: return
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

            task_index = self._frame_counter % 5
            if task_index == 0: self._process_presence(frame)
            elif task_index == 1 and FACE_REC_AVAILABLE: self._process_recognition(frame)
            elif task_index == 2 and MEDIAPIPE_AVAILABLE: self._process_gestures(frame)
            elif task_index == 3 and DEEPFACE_AVAILABLE: self._process_emotions(frame)
            elif task_index == 4 and YOLO_AVAILABLE: self._process_object_detection(frame)

            self._frame_counter += 1
            time.sleep(0.5) # Balance performance

    def _process_presence(self, frame):
        if not CV2_AVAILABLE: return
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
        if not self.known_face_encodings or not FACE_REC_AVAILABLE: return
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
        if not self.hands or not MEDIAPIPE_AVAILABLE: return
        self.detected_gesture = None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                try:
                    thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                    thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
                    index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
                    if (thumb_tip.x > thumb_ip.x and index_tip.y < index_pip.y):
                        self.detected_gesture = "open_palm"; break
                except Exception: pass

    def capture_and_read_text(self):
        if not PYTESSERACT_AVAILABLE: return "OCR is disabled due to missing libraries."
        if not self.camera or not self.camera.isOpened(): return "Camera not available."
        success, frame = self.camera.read()
        if not success: return "Failed to capture image."
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        try:
            text = pytesseract.image_to_string(thresh)
            return text if text.strip() else "I couldn't find any text."
        except Exception as e: return f"OCR Error: {e}"

    def _process_emotions(self, frame):
        if not DEEPFACE_AVAILABLE: return
        self.detected_emotion = None
        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(analysis, list) and len(analysis) > 0:
                self.detected_emotion = analysis[0]['dominant_emotion']
            elif isinstance(analysis, dict):
                self.detected_emotion = analysis['dominant_emotion']
        except Exception: pass

    def _process_object_detection(self, frame):
        """Analyzes a frame for common objects using YOLO."""
        if not self.yolo_model or not YOLO_AVAILABLE: return
        self.detected_objects = []
        try:
            results = self.yolo_model(frame, verbose=False)
            names = self.yolo_model.names
            for r in results:
                for c in r.boxes.cls:
                    self.detected_objects.append(names[int(c)])
            self.detected_objects = sorted(list(set(self.detected_objects)))
        except Exception as e:
            print(f"Object detection error: {e}")
            self.detected_objects = []
