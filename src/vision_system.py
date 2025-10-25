import cv2
import threading
import time

class VisionSystem:
    """
    Manages camera access and processes video frames for features like
    presence detection, gesture recognition, etc.
    """
    def __init__(self, motion_threshold=500000, presence_timeout=5.0):
        self.is_running = False
        self.camera = None
        self.vision_thread = None

        self.user_present = False
        self.last_motion_time = 0
        self.motion_threshold = motion_threshold  # How much change counts as motion
        self.presence_timeout = presence_timeout  # Seconds of no motion to be considered absent

        self._last_frame = None

    def start(self):
        """Initializes the camera and starts the vision processing thread."""
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

            # Convert to grayscale for easier processing
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

            if self._last_frame is None:
                self._last_frame = gray_frame
                continue

            # Calculate the difference between the current and last frame
            frame_delta = cv2.absdiff(self._last_frame, gray_frame)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

            # The sum of the white pixels is our motion score
            motion_score = cv2.sumElems(thresh)[0]

            if motion_score > self.motion_threshold:
                self.last_motion_time = time.time()
                self.user_present = True

            # If enough time has passed with no motion, assume user is absent
            if time.time() - self.last_motion_time > self.presence_timeout:
                self.user_present = False

            self._last_frame = gray_frame

            time.sleep(0.5)

if __name__ == '__main__':
    vision = VisionSystem()
    vision.start()

    try:
        print("Monitoring for user presence. Press Ctrl+C to stop.")
        while True:
            status = "Present" if vision.user_present else "Absent"
            print(f"User Status: {status} (Last motion: {round(time.time() - vision.last_motion_time, 2)}s ago)", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        vision.stop()
