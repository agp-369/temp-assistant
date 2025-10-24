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
from fuzzywuzzy import process
from dotenv import load_dotenv
from .app_mappings import APP_MAPPINGS, SEARCH_PATHS
from .command_parser import parse_command

load_dotenv()

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

if sys.platform == "win32":
    import win32gui
    import win32con
    import win32process
import win32com.client
import win32api

def resolve_shortcut(path):
    if path.lower().endswith(".lnk"):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(path)
            return shortcut.Targetpath
        except Exception as e:
            print(f"Error resolving shortcut {path}: {e}")
            return None
    return path

class Assistant:
    def __init__(self, output_callback=None):
        self.config = self.load_config()
        self.assistant_name = self.config.get("assistant_name", "Nora")
        self.wake_word = self.config.get("wake_word", "porcupine")
        self.output_callback = output_callback

        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.config.get("voice_options", {}).get("rate", 150))
        self.engine.setProperty('volume', self.config.get("voice_options", {}).get("volume", 0.9))

        self.recognizer = sr.Recognizer()
        self.waiting_for_confirmation = False
        self.pending_web_search_query = None

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

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

    def process_command(self, command_str):
        if self.waiting_for_confirmation:
            yes_match = process.extractOne(command_str, ["yes", "yeah", "yep"])
            no_match = process.extractOne(command_str, ["no", "nope", "nah"])

            if yes_match and yes_match[1] >= 80: # Threshold for 'yes'
                self.waiting_for_confirmation = False
                if self.pending_web_search_query:
                    self.perform_web_search(self.pending_web_search_query)
                    self.pending_web_search_query = None
                return True
            elif no_match and no_match[1] >= 80: # Threshold for 'no'
                self.waiting_for_confirmation = False
                self.pending_web_search_query = None
                self.speak("Okay, I won't search online.")
                return True
            else:
                self.speak("Please answer with yes or no.")
                return True

        else:
            # Check for out-of-context yes/no
            yes_match = process.extractOne(command_str, ["yes", "yeah", "yep"])
            no_match = process.extractOne(command_str, ["no", "nope", "nah"])

            if (yes_match and yes_match[1] >= 80) or (no_match and no_match[1] >= 80):
                self.speak("I'm not waiting for a yes or no response right now.")
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
        else:
            self.speak(f"Sorry, I don't know the command: {command_str}")
        return True

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

    def find_executable(self, app_name):
        platform = sys.platform
        app_name_lower = app_name.lower()
        mapped_names = APP_MAPPINGS.get(platform, {}).get(app_name_lower, [app_name])
        if not isinstance(mapped_names, list):
            mapped_names = [mapped_names]

        for mapped_name in mapped_names:
            # Check if the mapped name is an absolute path or directly executable
            if os.path.isfile(mapped_name) and os.access(mapped_name, os.X_OK):
                return mapped_name

            search_paths = os.environ.get("PATH", "").split(os.pathsep) + SEARCH_PATHS.get(platform, [])
            
            # Add common program files directories for Windows if not already present
            if platform == "win32":
                program_files = os.environ.get("PROGRAMFILES")
                program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
                local_app_data = os.environ.get("LOCALAPPDATA")

                if program_files and program_files not in search_paths:
                    search_paths.append(program_files)
                if program_files_x86 and program_files_x86 not in search_paths:
                    search_paths.append(program_files_x86)
                if local_app_data and os.path.join(local_app_data, 'Microsoft\\WindowsApps') not in search_paths:
                    search_paths.append(os.path.join(local_app_data, 'Microsoft\\WindowsApps'))

            for path in search_paths:
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower() == mapped_name.lower() or file.lower() == f"{mapped_name.lower()}.exe":
                            full_path = os.path.join(root, file)
                            resolved_path = resolve_shortcut(full_path) # Call resolve_shortcut
                            if resolved_path and os.path.isfile(resolved_path) and os.access(resolved_path, os.X_OK):
                                return resolved_path
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

    def get_process_pid(self, process_name):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
        return None

    def bring_window_to_front(self, pid):
        if sys.platform != "win32":
            self.speak("Bringing window to front is only supported on Windows for now.")
            return
        def enum_windows_callback(hwnd, pids):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != '':
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid in pids:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
        win32gui.EnumWindows(enum_windows_callback, [pid])

    def open_application(self, app_name):
        # 1. Try to find the executable and check if it's already running
        executable_path = self.find_executable(app_name)

        if executable_path:
            process_name = os.path.basename(executable_path)
            pid = self.get_process_pid(process_name)
            if pid:
                self.speak(f"Application '{app_name}' is already running. Bringing to front.")
                self.bring_window_to_front(pid)
                return # Application is already running and brought to front

            # If not running, launch it using subprocess.Popen
            try:
                if sys.platform == "win32":
                    subprocess.Popen([executable_path])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-a", executable_path])
                else:
                    subprocess.Popen([executable_path])
                self.speak(f"Opening {app_name}...")
                return
            except FileNotFoundError:
                self.speak(f"Error: The executable for {app_name} was found but could not be launched. It might be missing or corrupted.")
                return
            except OSError as e:
                if e.winerror == 193: # WinError 193: %1 is not a valid Win32 application
                    self.speak(f"Error: The file found for {app_name} is not a valid executable. Please check the installation.")
                else:
                    self.speak(f"An operating system error occurred while opening {app_name}: {e}")
                return
            except Exception as e:
                self.speak(f"An unexpected error occurred while opening {app_name}: {e}")
                return

        # 2. If find_executable failed, try ShellExecute
        try:
            win32api.ShellExecute(0, "open", app_name, "", "", win32con.SW_SHOWNORMAL)
            self.speak(f"Opening {app_name} using Windows ShellExecute...")
            return # Application launched successfully
        except Exception as e:
            self.speak(f"ShellExecute failed for {app_name}: {e}. Falling back to UWP/web search.")

        # 3. If ShellExecute also failed, try UWP app on Windows (unless it's whatsapp)
        if sys.platform == "win32" and app_name.lower() != "whatsapp":
            self.open_uwp_app(app_name)
            return

        # 4. If all else fails, ask about web search
        self.speak(f"Application '{app_name}' not found. Would you like to search online?")
        return "WAITING_FOR_WEB_SEARCH_CONFIRMATION"

    def close_application(self, app_name):
        executable_path = self.find_executable(app_name)
        if not executable_path:
            self.speak(f"Application '{app_name}' not found.")
            return

        process_name = os.path.basename(executable_path)
        matching_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                matching_pids.append(proc.info['pid'])

        if not matching_pids:
            self.speak(f"Application '{app_name}' is not running.")
            return

        closed_count = 0
        for pid in matching_pids:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=3)
                closed_count += 1
            except psutil.NoSuchProcess:
                pass # Already closed
            except psutil.TimeoutExpired:
                self.speak(f"Could not close {app_name} (PID: {pid}) gracefully. Forcing termination.")
                proc.kill()
                closed_count += 1
            except (psutil.AccessDenied, psutil.ZombieProcess):
                self.speak(f"Could not close {app_name} (PID: {pid}) due to system restrictions.")
            except Exception as e:
                self.speak(f"An error occurred while closing {app_name} (PID: {pid}): {e}")

        if closed_count > 0:
            self.speak(f"Successfully closed {closed_count} instance(s) of {app_name}.")
        else:
            self.speak(f"Could not close any instances of {app_name}.")

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
