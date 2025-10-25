import datetime
import subprocess
import sys
import os
import psutil
import webbrowser
import pyttsx3
import speech_recognition as sr
import pvporcupine
import pyaudio
import struct
import pyautogui
import json
import importlib.util
import threading
import time
import shutil
from dotenv import load_dotenv
from . import app_discovery
from . import window_manager
from . import custom_commands
from . import usage_tracker
from . import context_awareness
from . import web_interaction
from . import chitchat
from . import vision_system
from .command_parser import parse_command
from .plugin_interface import Plugin

load_dotenv()

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

if sys.platform == "win32":
    import win32api

class Assistant:
    def __init__(self, output_callback=None):
        # Initialization and Configuration
        self.config = self.load_config()
        self.assistant_name = self.config.get("assistant_name", "Nora")
        self.wake_word = self.config.get("wake_word", "porcupine")
        self.output_callback = output_callback
        self.apps = app_discovery.load_cached_apps()
        self.custom_commands = custom_commands.load_commands()
        self.plugins, self.plugin_command_map = self.load_plugins()

        # Voice Engine Setup
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.config.get("voice_options", {}).get("rate", 150))
        self.engine.setProperty('volume', self.config.get("voice_options", {}).get("volume", 0.9))

        # Speech Recognition Setup
        self.recognizer = sr.Recognizer()
        self.waiting_for_confirmation = False
        self.pending_web_search_query = None
        self.pending_file_move = None

        # Conversational AI history
        self.conversation_history = None

        # Vision System
        self.vision = vision_system.VisionSystem()
        self.vision.start()
        self.auto_lock_thread = threading.Thread(target=self._auto_lock_loop, daemon=True)
        self.auto_lock_thread.start()
        self.greeting_thread = threading.Thread(target=self._greeting_loop, daemon=True)
        self.greeting_thread.start()
        self.gesture_thread = threading.Thread(target=self._gesture_control_loop, daemon=True)
        self.gesture_thread.start()

        self.context_thread = threading.Thread(target=self._context_awareness_loop, daemon=True)
        self.context_thread.start()

    # --- Configuration ---
    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_plugins(self):
        """
        Loads plugins from the 'plugins' directory and builds a command map.
        Returns a list of all plugins and a dictionary mapping intents to plugins.
        """
        plugins = []
        command_map = {}
        if not os.path.exists("plugins"):
            return plugins, command_map

        for filename in os.listdir("plugins"):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"plugins.{filename[:-3]}"
                spec = importlib.util.spec_from_file_location(module_name, os.path.join("plugins", filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type) and issubclass(attribute, Plugin) and attribute is not Plugin:
                        plugin_instance = attribute()
                        plugins.append(plugin_instance)
                        # Register commands that the plugin handles by intent
                        if hasattr(plugin_instance, "get_intent_map"):
                            for intent in plugin_instance.get_intent_map():
                                command_map[intent] = plugin_instance
        return plugins, command_map

    # --- Voice and Speech ---
    def speak(self, text, is_error=False):
        """Outputs text to the GUI or console, handling errors."""
        if is_error:
            text = f"Error: {text}"

        if self.output_callback:
            self.output_callback(text)
        else:
            print(f"{self.assistant_name}: {text}")

        # Voice output can be unreliable in some environments, so we wrap it
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def listen_for_wake_word(self):
        if not PICOVOICE_ACCESS_KEY:
            self.speak("Picovoice access key not found. Please set the PICOVOICE_ACCESS_KEY environment variable.")
            return

        porcupine = None
        pa = None
        audio_stream = None
        try:
            porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keywords=[self.wake_word])
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )
            print(f"Listening for wake word ('{self.wake_word}')...")
            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    print("Wake word detected!")
                    command = self.listen_for_command()
                    if command:
                        if not self.process_command(command):
                            break # Exit loop if process_command signals to
        except Exception as e:
            self.speak(f"An error occurred with the wake word listener: {e}", is_error=True)
        finally:
            if audio_stream is not None:
                audio_stream.close()
            if pa is not None:
                pa.terminate()
            if porcupine is not None:
                porcupine.delete()

    def listen_for_command(self):
        with sr.Microphone() as source:
            print("Listening for command...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            command = self.recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't catch that.")
            return None
        except sr.RequestError:
            self.speak("Sorry, my speech service is down.")
            return None

    # --- Command Processing ---
    def process_command(self, command_str):
        if self.waiting_for_confirmation:
            if "yes" in command_str:
                self.waiting_for_confirmation = False
                if hasattr(self, 'pending_summarization_url'):
                    self.summarize_page(self.pending_summarization_url)
                    del self.pending_summarization_url
                elif self.pending_web_search_query:
                    self.perform_web_search(self.pending_web_search_query)
                    self.pending_web_search_query = None
                elif self.pending_file_move:
                    self.execute_file_move()
            elif "no" in command_str:
                self.waiting_for_confirmation = False
                self.pending_web_search_query = None
                self.pending_file_move = None
                if hasattr(self, 'pending_summarization_url'):
                    del self.pending_summarization_url
                self.speak("Okay, I won't do that.")
            else:
                self.speak("Please answer with yes or no.")
            return True

        # Check for custom commands first
        if command_str in self.custom_commands:
            actions = self.custom_commands[command_str]
            for action in actions:
                self.process_command(action)
            return True

        # Check for plugin commands
        for plugin in self.plugins:
            if plugin.can_handle(command_str):
                plugin.handle(command_str, self)
                return True

        command, args = parse_command(command_str)

        # Check for intent-based plugin commands
        if command in self.plugin_command_map:
            plugin = self.plugin_command_map[command]
            plugin.handle((command, args), self)
            return True

        if command == "exit":
            self.speak("Goodbye!")
            return False # Signal to exit
        elif command == "open_app":
            result = self.open_application(args)
            if result == "WAITING_FOR_WEB_SEARCH_CONFIRMATION":
                self.waiting_for_confirmation = True
                self.pending_web_search_query = args # Store the app_name for later search
            return True # Always return True here, as we might be waiting for confirmation
        elif command == "close_app":
            self.close_application(args)
        elif command == "open_file":
            self.open_file(args)
        elif command == "play_youtube":
            self.play_on_youtube(args)
        elif command == "type_text":
            self.type_text(args)
        elif command == "search":
            self.perform_web_search(args)
        elif command == "get_time":
            self.get_time()
        elif command == "get_weather":
            self.get_weather(args)
        elif command == "greet":
            self.get_greeting()
        elif command == "get_date":
            self.get_date()
        elif command == "open_uwp_app_direct":
            self.open_uwp_app_direct(args)
        elif command == "teach_command":
            command_name, actions = args
            self.teach_command(command_name, actions)
        elif command == "answer_question":
            self.answer_question(args)
        elif command == "learn_face":
            self.speak("Learning your face... Please look at the camera.")
            response = self.vision.learn_current_user_face(args)
            self.speak(response)
        else:
            # If no other command was matched, try the conversational AI
            response, self.conversation_history = chitchat.get_chitchat_response(command_str, self.conversation_history)
            self.speak(response)
        return True

    def answer_question(self, query):
        """Answers a direct question using the web_interaction module."""
        self.speak(f"Looking up {query}...")
        answer = web_interaction.get_instant_answer(query)
        if answer:
            self.speak(answer)
        else:
            self.speak(f"I couldn't find a direct answer for '{query}'. I'll perform a web search for you.")
            self.perform_web_search(query)

    # --- Core Commands ---
    def teach_command(self, name, actions):
        """Teaches the assistant a new command."""
        if custom_commands.save_command(name, actions):
            self.custom_commands = custom_commands.load_commands()  # Reload commands
            self.speak(f"I've learned a new command: '{name}'.")
        else:
            self.speak("I'm sorry, I couldn't save that command.")

    def summarize_page(self, url):
        """Summarizes the content of a web page."""
        self.speak("Okay, summarizing the page.")
        content = web_interaction.get_page_content(url)
        if not content:
            self.speak("I was unable to retrieve the content from the page.")
            return

        summary = web_interaction.summarize_text(content)
        if not summary:
            self.speak("I'm sorry, I couldn't summarize the content.")
        else:
            self.speak(summary)

    def perform_web_search(self, query):
        self.speak(f"Searching online for {query}.")
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            webbrowser.open(search_url)
        except Exception as e:
            self.speak(f"Could not open web browser to search online: {e}")

    def get_time(self):
        now = datetime.datetime.now()
        self.speak(f"The current time is {now.strftime('%I:%M %p')}")

    def get_weather(self, location):
        self.speak(f"To get weather information, I need to integrate with a weather API. Please provide an API key or specify your preferred weather service. For now, I can't tell the weather for {location}.")

    def get_greeting(self):
        self.speak("Hello there! How can I help you today?")

    def get_date(self):
        today = datetime.date.today()
        self.speak(f"Today's date is {today.strftime('%B %d, %Y')}")

    def open_uwp_app_direct(self, app_id):
        try:
            subprocess.run(f'start shell:appsfolder\\{app_id}', shell=True, check=True)
            self.speak(f"Opening UWP app with ID: {app_id}...")
        except subprocess.CalledProcessError:
            self.speak(f"Could not open the UWP app with ID: {app_id}. Please ensure the ID is correct.")
        except Exception as e:
            self.speak(f"An error occurred while opening UWP app: {e}")

    def type_text(self, text):
        try:
            self.speak(f"Typing: {text}")
            pyautogui.write(text, interval=0.05)
        except Exception as e:
            self.speak(f"An error occurred while typing: {e}")

    def _context_awareness_loop(self):
        """Periodically checks the user's context and offers help."""
        while True:
            time.sleep(5)
            if self.waiting_for_confirmation:
                continue

            info = context_awareness.get_active_window_info()
            if info:
                process_name = info.get("process_name", "").lower()
                if process_name in ["chrome.exe", "firefox.exe", "msedge.exe"]:
                    url = context_awareness.get_browser_url(process_name)
                    if url:
                        self.speak("I see you're on a web page. Would you like me to summarize it for you?")
                        self.waiting_for_confirmation = True
                        self.pending_summarization_url = url

    def _find_best_match(self, query, items, usage_stats):
        """Finds the best match for a query from a list of items based on usage."""
        # Simple implementation: prioritize exact match, then most used
        query_lower = query.lower()
        if query_lower in items:
            return items[query_lower]

        # Find all partial matches
        matches = {name: path for name, path in items.items() if query_lower in name}
        if not matches:
            return None

        # Prioritize by usage
        if usage_stats:
            best_match_name = max(matches.keys(), key=lambda name: usage_stats.get(name, 0))
            return matches[best_match_name]

        # If no usage stats, return the first match
        return list(matches.values())[0]

    # --- File System and Applications ---
    def find_executable(self, app_name):
        stats = usage_tracker.load_stats()
        return self._find_best_match(app_name, self.apps, stats.get("apps"))

    def find_file(self, filename):
        # This is a simplified version; a real implementation would search the file system
        # and then use the usage stats to prioritize. For now, we'll just use a placeholder.
        home_dir = os.path.expanduser("~")
        all_files = {}
        for root, _, files in os.walk(home_dir):
            for file in files:
                all_files[file.lower()] = os.path.join(root, file)

        stats = usage_tracker.load_stats()
        return self._find_best_match(filename, all_files, stats.get("files"))

    def open_uwp_app(self, app_name):
        try:
            subprocess.run(f'start shell:appsfolder\\{app_name}', shell=True, check=True)
            self.speak(f"Opening {app_name}...")
        except subprocess.CalledProcessError:
            self.speak(f"Could not open the UWP app: {app_name}. It might not be installed, or the app name is incorrect.")


    def open_application(self, app_name):
        # 1. Try to bring the window to the front if it's already open
        if window_manager.bring_window_to_front(app_name):
            self.speak(f"Application '{app_name}' is already running. Bringing to front.")
            usage_tracker.track_app_usage(app_name)
            return

        # 2. If not open, find the executable
        executable_path = self.find_executable(app_name)
        if executable_path:
            try:
                subprocess.Popen([executable_path])
                self.speak(f"Opening {app_name}...")
                usage_tracker.track_app_usage(app_name)
            except Exception as e:
                self.speak(f"An unexpected error occurred while opening {app_name}: {e}")
            return

        # 3. If executable not found, try other platform-specific methods
        try:
            if sys.platform == "win32":
                win32api.ShellExecute(0, "open", app_name, "", "", 1)
                self.speak(f"Opening {app_name} using Windows ShellExecute...")
                return
            elif sys.platform == "darwin": # macOS
                subprocess.Popen(["open", "-a", app_name])
                self.speak(f"Opening {app_name}...")
                return
            else: # Linux and other OS
                # This is a simple approach; a more robust solution would search PATH
                subprocess.Popen([app_name])
                self.speak(f"Opening {app_name}...")
                return
        except Exception:
             # 4. If all else fails, ask about web search
            self.speak(f"Application '{app_name}' not found. Would you like to search online?")
        return "WAITING_FOR_WEB_SEARCH_CONFIRMATION"

    def close_application(self, app_name):
        if window_manager.close_window(app_name):
            self.speak(f"Successfully closed {app_name}.")
        else:
            self.speak(f"Could not find or close the application '{app_name}'. It might not be running.")

    def open_file(self, filename):
        filepath = self.find_file(filename)
        if not filepath:
            self.speak(f"File '{filename}' not found in your home directory.")
            return
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
            self.speak(f"Opening {filename}...")
            usage_tracker.track_file_usage(filename)
        except Exception as e:
            self.speak(str(e), is_error=True)

    def execute_file_move(self):
        """Executes the pending file move operation after confirmation."""
        if not self.pending_file_move:
            return

        files = self.pending_file_move["files"]
        dest = self.pending_file_move["dest"]
        moved_count = 0

        try:
            for f in files:
                shutil.move(f, dest)
                moved_count += 1
            self.speak(f"Successfully moved {moved_count} files.")
        except Exception as e:
            self.speak(f"An error occurred while moving files: {e}", is_error=True)
        finally:
            self.pending_file_move = None

    def lock_screen(self):
        """Locks the user's screen."""
        self.speak("User is absent. Locking screen.")
        try:
            if sys.platform == "win32":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            elif sys.platform == "darwin": # macOS
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
            else: # Linux
                subprocess.run(["xdg-screensaver", "lock"])
        except Exception as e:
            self.speak(f"Failed to lock screen: {e}", is_error=True)

    def _auto_lock_loop(self):
        """Periodically checks for user absence and locks the screen."""
        lock_delay = self.config.get("auto_lock_delay_seconds", 30)
        last_present_time = time.time()
        is_locked = False

        while True:
            if self.vision.user_present:
                last_present_time = time.time()
                is_locked = False
            else:
                if not is_locked and (time.time() - last_present_time) > lock_delay:
                    self.lock_screen()
                    is_locked = True

            time.sleep(5) # Check every 5 seconds

    def _greeting_loop(self):
        """Periodically checks for a recognized user and greets them."""
        greeted_users = []
        while True:
            if self.vision.recognized_user and self.vision.recognized_user not in greeted_users:
                name = self.vision.recognized_user
                self.speak(f"Welcome back, {name}!")
                greeted_users.append(name)

            # Reset if no user is present
            if not self.vision.user_present:
                greeted_users = []

            time.sleep(3)

    def _gesture_control_loop(self):
        """Periodically checks for gestures and performs actions."""
        while True:
            if self.vision.detected_gesture == "open_palm":
                self.speak("Open palm detected, pausing media.")
                pyautogui.press('space')
                self.vision.detected_gesture = None # Clear gesture after handling

            time.sleep(1) # Check for gestures every second

    def play_on_youtube(self, query):
        """Searches for and plays a video on YouTube."""
        if not query:
            self.speak("What would you like me to play on YouTube?")
            return

        self.speak(f"Playing {query} on YouTube.")
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        try:
            webbrowser.open(search_url)
        except Exception as e:
            self.speak(f"Could not open web browser to play on YouTube: {e}", is_error=True)
