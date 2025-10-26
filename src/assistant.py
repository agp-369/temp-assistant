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
from . import app_discovery, window_manager, custom_commands, usage_tracker
from . import context_awareness, web_interaction, chitchat, vision_system
from .command_parser import parse_command
from .plugin_interface import Plugin
from . import task_planner
from . import memory_manager

load_dotenv()

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

if sys.platform == "win32":
    import win32api

class Assistant:
    def __init__(self, output_callback=None):
        # ... (most init is the same)
        self.config = self.load_config()
        self.assistant_name = self.config.get("assistant_name", "Nora")
        self.wake_word = self.config.get("wake_word", "porcupine")
        self.output_callback = output_callback
        self.apps = app_discovery.load_cached_apps()
        self.custom_commands = custom_commands.load_commands()
        self.plugins, self.plugin_command_map = self.load_plugins()

        # Cognitive Core
        self.planner = task_planner.TaskPlanner(self)
        self.memory = memory_manager.MemoryManager()
        self.last_summary = None # To pass context between plan steps

        # Voice Engine, SR, and other setups...
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.recognizer = sr.Recognizer()
        self.waiting_for_confirmation = False
        self.pending_web_search_query = None
        self.pending_file_move = None
        self.pending_text_summarization = None
        self.conversation_history = None
        self.vision = vision_system.VisionSystem()
        self.vision.start()

        # Start all background threads
        self.threads = {
            "auto_lock": threading.Thread(target=self._auto_lock_loop, daemon=True),
            "greeting": threading.Thread(target=self._greeting_loop, daemon=True),
            "gesture": threading.Thread(target=self._gesture_control_loop, daemon=True),
            "mood": threading.Thread(target=self._mood_awareness_loop, daemon=True),
            "context": threading.Thread(target=self._context_awareness_loop, daemon=True)
        }
        for thread in self.threads.values():
            thread.start()

    # ... (speak, load_config, load_plugins, listen methods are the same)
    def speak(self, text, is_error=False):
        if is_error: text = f"Error: {text}"
        if self.output_callback: self.output_callback(text)
        else: print(f"{self.assistant_name}: {text}")
        try: self.engine.say(text); self.engine.runAndWait()
        except Exception as e: print(f"TTS Error: {e}")
    # ... other methods unchanged until process_command

    def process_command(self, command_str, from_plan=False):
        # Add conversation to memory *unless* it's a confirmation
        if not self.waiting_for_confirmation:
            self.memory.add_to_memory(f"User: {command_str}")

        if self.waiting_for_confirmation:
            # ... (confirmation logic is the same)
            if "yes" in command_str:
                self.waiting_for_confirmation = False
                if hasattr(self, 'pending_summarization_url'):
                    self.summarize_page(self.pending_summarization_url, from_plan=True)
                elif self.pending_web_search_query:
                    self.perform_web_search(self.pending_web_search_query)
                elif self.pending_file_move:
                    self.execute_file_move()
                elif self.pending_text_summarization:
                    summary = web_interaction.summarize_text(self.pending_text_summarization)
                    self.speak(summary)
                    self.last_summary = summary # Save for planner
                    self.pending_text_summarization = None
            elif "no" in command_str:
                self.waiting_for_confirmation = False # Reset all pending
                self.pending_web_search_query = None
                self.pending_file_move = None
                self.pending_text_summarization = None
                if hasattr(self, 'pending_summarization_url'): del self.pending_summarization_url
                self.speak("Okay, I won't do that.")
            else: self.speak("Please answer with yes or no.")
            return True

        # --- Cognitive Hierarchy ---

        # 1. Custom Commands (Highest Priority)
        if command_str in self.custom_commands:
            actions = self.custom_commands[command_str]
            for action in actions: self.process_command(action)
            return True

        # 2. Direct NLP Intent Matching
        command, args = parse_command(command_str)
        if command:
            # Keyword-based plugins
            for plugin in self.plugins:
                if plugin.can_handle(command_str):
                    plugin.handle(command_str, self)
                    return True
            # Intent-based plugins
            if command in self.plugin_command_map:
                plugin = self.plugin_command_map[command]
                plugin.handle((command, args), self)
                return True
            # Core commands
            if self.handle_core_command(command, args):
                return True

        # 3. Task Planner
        if not from_plan: # Avoid recursive planning
            plan = self.planner.create_plan(command_str)
            if plan:
                self.planner.execute_plan(plan)
                return True

        # 4. Memory/Context-based Fallback (for follow-up questions)
        # Placeholder - a real implementation would use LLM with context

        # 5. Chitchat Fallback (Lowest Priority)
        response, self.conversation_history = chitchat.get_chitchat_response(command_str, self.conversation_history)
        self.speak(response)
        self.memory.add_to_memory(f"Nora: {response}")
        return True

    def handle_core_command(self, command, args):
        """Handles the built-in, non-plugin commands."""
        handlers = {
            "exit": lambda a: self.speak("Goodbye!"),
            "open_app": self.open_application,
            "close_app": self.close_application,
            "open_file": self.open_file,
            "play_youtube": self.play_on_youtube,
            "type_text": self.type_text,
            "search": self.perform_web_search,
            "get_time": self.get_time,
            "get_weather": self.get_weather, # Should be a plugin, here for legacy
            "greet": self.get_greeting,
            "get_date": self.get_date,
            "teach_command": lambda a: self.teach_command(a[0], a[1]),
            "answer_question": self.answer_question,
            "learn_face": lambda a: self.speak(self.vision.learn_current_user_face(a)),
            "read_text": self.handle_read_text,
            "identify_objects": self.handle_identify_objects
        }
        if command in handlers:
            if command == "teach_command":
                handlers[command](args)
            elif command == "exit":
                handlers[command](args)
                return False # Signal exit
            else:
                handlers[command](args)
            return True
        return False

    # ... (Other command implementations: answer_question, teach_command, etc.)
    # Minor modifications needed for planner integration
    def summarize_page(self, url, from_plan=False):
        self.speak("Okay, summarizing the page.")
        content = web_interaction.get_page_content(url)
        if not content: self.speak("I couldn't get the content."); return
        summary = web_interaction.summarize_text(content)
        self.last_summary = summary # Save for planner
        self.speak(summary)

    def handle_read_text(self, args):
        self.speak("Okay, please hold the text up to the camera.")
        extracted_text = self.vision.capture_and_read_text()
        if "couldn't" in extracted_text or "Error" in extracted_text:
            self.speak(extracted_text, is_error=True)
        else:
            self.speak("I found the following text:"); self.speak(extracted_text[:150] + "...")
            self.speak("Would you like me to summarize this text?")
            self.waiting_for_confirmation = True
            self.pending_text_summarization = extracted_text

    def handle_identify_objects(self, args):
        objects = self.vision.detected_objects
        if not objects: self.speak("I don't see any recognizable objects.")
        else: self.speak(f"I can see a {', a '.join(objects)}.")

    # ... (rest of the assistant's methods are largely unchanged)
    def open_application(self, app_name):
        if window_manager.bring_window_to_front(app_name):
            self.speak(f"'{app_name}' is already running."); return
        executable_path = self.find_executable(app_name)
        if executable_path:
            try: subprocess.Popen([executable_path]); self.speak(f"Opening {app_name}...")
            except Exception as e: self.speak(f"Error opening {app_name}: {e}", is_error=True)
            return
        # ... platform specific fallbacks
        self.speak(f"Application '{app_name}' not found. Would you like to search online?")
        self.waiting_for_confirmation = True
        self.pending_web_search_query = app_name
    def close_application(self, app_name):
        if not window_manager.close_window(app_name):
            self.speak(f"Could not find or close '{app_name}'.")
        else: self.speak(f"Closed {app_name}.")
    def open_file(self, filename):
        filepath = self.find_file(filename)
        if not filepath: self.speak(f"File '{filename}' not found."); return
        try:
            if sys.platform == "win32": os.startfile(filepath)
            elif sys.platform == "darwin": subprocess.Popen(["open", filepath])
            else: subprocess.Popen(["xdg-open", filepath])
            self.speak(f"Opening {filename}...")
        except Exception as e: self.speak(str(e), is_error=True)
    def execute_file_move(self):
        if not self.pending_file_move: return
        files, dest = self.pending_file_move["files"], self.pending_file_move["dest"]
        moved_count = 0
        try:
            for f in files: shutil.move(f, dest); moved_count += 1
            self.speak(f"Successfully moved {moved_count} files.")
        except Exception as e: self.speak(f"Error moving files: {e}", is_error=True)
        finally: self.pending_file_move = None
    def lock_screen(self):
        self.speak("User absent. Locking screen.")
        try:
            if sys.platform == "win32": import ctypes; ctypes.windll.user32.LockWorkStation()
            elif sys.platform == "darwin": subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
            else: subprocess.run(["xdg-screensaver", "lock"])
        except Exception as e: self.speak(f"Failed to lock screen: {e}", is_error=True)
    def _auto_lock_loop(self):
        lock_delay = self.config.get("auto_lock_delay_seconds", 30)
        last_present_time = time.time(); is_locked = False
        while True:
            if self.vision.user_present: last_present_time = time.time(); is_locked = False
            else:
                if not is_locked and (time.time() - last_present_time) > lock_delay:
                    self.lock_screen(); is_locked = True
            time.sleep(5)
    def _greeting_loop(self):
        greeted_users = []
        while True:
            if self.vision.recognized_user and self.vision.recognized_user not in greeted_users:
                name = self.vision.recognized_user; self.speak(f"Welcome back, {name}!"); greeted_users.append(name)
            if not self.vision.user_present: greeted_users = []
            time.sleep(3)
    def _gesture_control_loop(self):
        while True:
            if self.vision.detected_gesture == "open_palm":
                self.speak("Open palm detected, pausing media."); pyautogui.press('space'); self.vision.detected_gesture = None
            time.sleep(1)
    def _mood_awareness_loop(self):
        suggestion_made = False
        while True:
            if self.vision.user_present and not suggestion_made:
                emotion = self.vision.detected_emotion
                if emotion in ["sad", "neutral"]:
                    self.speak("You seem a bit down. Would you like me to play some uplifting music?")
                    self.waiting_for_confirmation = True
                    self.pending_web_search_query = "uplifting instrumental music"; suggestion_made = True
            if not self.vision.user_present: suggestion_made = False
            time.sleep(10)
    def play_on_youtube(self, query):
        if not query: self.speak("What should I play?"); return
        self.speak(f"Playing {query} on YouTube.")
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        try: webbrowser.open(search_url)
        except Exception as e: self.speak(f"Could not open web browser: {e}", is_error=True)
    # ... (other core commands)
    def get_time(self): self.speak(f"The time is {datetime.datetime.now().strftime('%I:%M %p')}.")
    def get_date(self): self.speak(f"Today is {datetime.date.today().strftime('%B %d, %Y')}.")
    def get_greeting(self): self.speak("Hello! How can I help?")
    # ... (And so on for other simple commands)
