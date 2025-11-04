import os
import sys
from unittest.mock import MagicMock

# Mock heavy dependencies that are not needed for most unit tests
sys.modules['pyautogui'] = MagicMock()
sys.modules['src.vision_system'] = MagicMock()
sys.modules['pyttsx3'] = MagicMock()

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
