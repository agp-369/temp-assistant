import threading
import time
from src.plugin_interface import Plugin
import re
import src.notification_manager as notification_manager

class AlarmsPlugin(Plugin):
    """
    A plugin to handle alarms and reminders.
    """
    def __init__(self):
        self.alarms = []

    def get_intent_map(self):
        return {
            "set_reminder": self.handle,
            "set_alarm": self.handle
        }

    def can_handle(self, command):
        return False # This plugin is intent-based

    def _parse_time(self, time_str):
        """Parses a simple time string (e.g., 'in 5 minutes', 'at 10:30 pm')."""
        # This is a very simple parser. A more robust solution would use a dedicated library.
        time_str = time_str.lower()

        # Case 1: "in X minutes/seconds/hours"
        match = re.search(r'in (\d+) (minute|second|hour)s?', time_str)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if unit == "minute":
                return value * 60
            elif unit == "second":
                return value
            elif unit == "hour":
                return value * 3600

        return None # Placeholder for more complex parsing

    def _set_timer(self, delay, message, assistant):
        """Sets a timer to speak a message and send a notification after a delay."""
        def on_timer_end():
            assistant.speak(message)
            notification_manager.send_notification("Nora Reminder", message)
            # Remove timer from active list
            self.alarms = [a for a in self.alarms if a.ident != threading.current_thread().ident]

        timer = threading.Timer(delay, on_timer_end)
        timer.start()
        self.alarms.append(timer)

    def handle(self, command, assistant):
        intent, args = command

        # The argument should contain both the message and the time string
        # e.g., "to buy milk in 5 minutes"
        time_str_match = re.search(r'(in \d+ (?:minute|second|hour)s?|at \d{1,2}:\d{2} ?(?:am|pm)?)', args)
        if not time_str_match:
            assistant.speak("I'm sorry, I didn't understand the time for the reminder.")
            return

        time_str = time_str_match.group(0)
        message = args.replace(time_str, "").strip()

        delay = self._parse_time(time_str)
        if delay is None:
            assistant.speak("I'm sorry, I couldn't parse that time format yet.")
            return

        full_message = ""
        if intent == "set_reminder":
            full_message = f"Reminder: {message}"
        elif intent == "set_alarm":
            full_message = f"Alarm: {message}"

        self._set_timer(delay, full_message, assistant)
        assistant.speak(f"Okay, I will remind you {time_str}.")
