from src.plugin_interface import Plugin
import psutil
import time
from src import notification_manager

class SystemMonitorPlugin(Plugin):
    """
    A plugin to monitor system status like CPU, memory, and battery.
    """
    def __init__(self):
        self.last_battery_alert_time = 0
        # Alert every 10 minutes if the condition persists
        self.battery_alert_cooldown = 600

    def get_intent_map(self):
        return {
            "get_cpu_usage": self.handle,
            "get_memory_usage": self.handle,
            "get_battery_status": self.handle
        }

    def can_handle(self, command):
        return False # This plugin is intent-based

    def get_cpu_usage(self):
        """Returns the current CPU usage percentage."""
        return f"Current CPU usage is at {psutil.cpu_percent()}%."

    def get_memory_usage(self):
        """Returns the current memory usage percentage."""
        memory_info = psutil.virtual_memory()
        return f"Current memory usage is at {memory_info.percent}%."

    def get_battery_status(self):
        """Returns the battery status, if available."""
        battery = psutil.sensors_battery()
        if battery:
            plugged = "plugged in" if battery.power_plugged else "not plugged in"
            return f"Battery is at {battery.percent}%, and is {plugged}."
        else:
            return "No battery detected in the system."

    def check_battery_alert(self):
        """Checks for low battery and sends a notification if needed."""
        battery = psutil.sensors_battery()
        if battery:
            is_low = battery.percent < 20
            is_unplugged = not battery.power_plugged
            cooldown_passed = (time.time() - self.last_battery_alert_time) > self.battery_alert_cooldown

            if is_low and is_unplugged and cooldown_passed:
                notification_manager.send_notification(
                    "Low Battery Warning",
                    f"Battery is at {battery.percent}%. Please plug in your device."
                )
                self.last_battery_alert_time = time.time()

    def handle(self, command, assistant):
        # This handle method will be called directly by the assistant
        # based on the parsed intent.
        intent, _ = command # Unpack the intent and args tuple

        if intent == "get_cpu_usage":
            assistant.speak(self.get_cpu_usage())
        elif intent == "get_memory_usage":
            assistant.speak(self.get_memory_usage())
        elif intent == "get_battery_status":
            assistant.speak(self.get_battery_status())
        else:
            assistant.speak("Sorry, I don't know how to handle that system command.")
