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
from dotenv import load_dotenv
from . import app_discovery
from . import window_manager
from . import custom_commands
from . import web_interaction
from .command_parser import parse_command

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

        # Voice Engine Setup
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.config.get("voice_options", {}).get("rate", 150))
        self.engine.setProperty('volume', self.config.get("voice_options", {}).get("volume", 0.9))

        # Speech Recognition Setup
        self.recognizer = sr.Recognizer()
        self.waiting_for_confirmation = False
        self.pending_web_search_query = None

    # --- Configuration ---
    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    # --- Voice and Speech ---
    def speak(self, text):
        if self.output_callback:
            self.output_callback(text)
        else:
            print(f"{self.assistant_name}: {text}")
            self.engine.say(text)
            self.engine.runAndWait()

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
            self.speak(f"An error occurred with the wake word listener: {e}")
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
                if self.pending_web_search_query:
                    self.perform_web_search(self.pending_web_search_query)
                    self.pending_web_search_query = None
            elif "no" in command_str:
                self.waiting_for_confirmation = False
                self.pending_web_search_query = None
                self.speak("Okay, I won't search online.")
            else:
                self.speak("Please answer with yes or no.")
            return True

        # Check for custom commands first
        if command_str in self.custom_commands:
            actions = self.custom_commands[command_str]
            for action in actions:
                self.process_command(action)
            return True

        command, args = parse_command(command_str)

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
        else:
            self.speak(f"Sorry, I don't know the command: {command_str}")
        return True

    # --- Core Commands ---
    def teach_command(self, name, actions):
        """Teaches the assistant a new command."""
        if custom_commands.save_command(name, actions):
            self.custom_commands = custom_commands.load_commands()  # Reload commands
            self.speak(f"I've learned a new command: '{name}'.")
        else:
            self.speak("I'm sorry, I couldn't save that command.")

    def perform_web_search(self, query):
        self.speak(f"Searching for {query}...")
        results = web_interaction.get_search_results(query)
        if not results:
            self.speak("I couldn't find any results online.")
            return

        # For simplicity, we'll use the first result
        top_result_url = results[0]
        self.speak("Here's a summary of the top result:")

        content = web_interaction.get_page_content(top_result_url)
        if not content:
            self.speak("I was unable to retrieve the content from the page.")
            return

        summary = web_interaction.summarize_text(content)
        if not summary:
            self.speak("I'm sorry, I couldn't summarize the content.")
        else:
            self.speak(summary)

        # Also open the browser to the search results
        try:
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        except Exception as e:
            self.speak(f"I encountered an error opening the web browser: {e}")

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

    # --- File System and Applications ---
    def find_executable(self, app_name):
        app_name_lower = app_name.lower()
        # Search in the cached app list
        if app_name_lower in self.apps:
            return self.apps[app_name_lower]

        # Fallback to searching the system PATH
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, app_name)
            if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
                return exe_file

        return None

    def find_file(self, filename):
        home_dir = os.path.expanduser("~")
        for root, _, files in os.walk(home_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

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
            return

        # 2. If not open, find the executable
        executable_path = self.find_executable(app_name)
        if executable_path:
            try:
                subprocess.Popen([executable_path])
                self.speak(f"Opening {app_name}...")
            except Exception as e:
                self.speak(f"An unexpected error occurred while opening {app_name}: {e}")
            return

        # 3. If executable not found, try other methods (ShellExecute, UWP)
        if sys.platform == "win32":
            try:
                win32api.ShellExecute(0, "open", app_name, "", "", 1)
                self.speak(f"Opening {app_name} using Windows ShellExecute...")
                return
            except Exception:
                # If ShellExecute fails, try to open as a UWP app
                self.open_uwp_app(app_name)
                return

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
        except Exception as e:
            self.speak(f"An error occurred: {e}")

    def play_on_youtube(self, query):
        self.speak(f"Playing {query} on YouTube.")
        try:
            webbrowser.open(search_url)
        except Exception as e:
            self.speak(f"Could not open web browser to play on YouTube: {e}")
