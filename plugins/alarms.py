import threading
import time
from src.plugin_interface import Plugin
import re
import datetime
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
        """Parses a time string (e.g., 'in 5 minutes', 'at 10:30 pm')."""
        time_str = time_str.lower()

        # Case 1: "in X minutes/seconds/hours"
        match_in = re.search(r'in (\d+) (minute|second|hour)s?', time_str)
        if match_in:
            value = int(match_in.group(1))
            unit = match_in.group(2)
            if unit == "minute": return value * 60
            if unit == "second": return value
            if unit == "hour": return value * 3600

        # Case 2: "at HH:MM am/pm"
        match_at = re.search(r'at (\d{1,2}):(\d{2}) ?(am|pm)?', time_str)
        if match_at:
            hour = int(match_at.group(1))
            minute = int(match_at.group(2))
            ampm = match_at.group(3)

            if ampm == 'pm' and hour < 12:
                hour += 12
            if ampm == 'am' and hour == 12: # Midnight case
                hour = 0

            now = datetime.datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the time is in the past, assume it's for the next day
            if target_time < now:
                target_time += datetime.timedelta(days=1)

            delay_seconds = (target_time - now).total_seconds()
            return delay_seconds

        return None

    def _set_timer(self, delay, message, assistant):
        # ... (same as before)
        def on_timer_end():
            assistant.speak(message)
            notification_manager.send_notification("Nora Reminder", message)
            self.alarms = [a for a in self.alarms if a.ident != threading.current_thread().ident]
        timer = threading.Timer(delay, on_timer_end)
        timer.start()
        self.alarms.append(timer)

    def handle(self, command, assistant):
        # ... (same as before)
        intent, args = command
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
        full_message = f"{intent.replace('_', ' ').title()}: {message}"
        self._set_timer(delay, full_message, assistant)
        assistant.speak(f"Okay, I will remind you {time_str}.")
