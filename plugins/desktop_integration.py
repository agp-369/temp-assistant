import time
import os
from src.plugin_interface import Plugin
from src import window_manager

class DesktopIntegrationPlugin(Plugin):
    """
    A plugin to handle integrations with desktop applications like WhatsApp.
    """
    def get_intent_map(self):
        return {
            "send_whatsapp": self.send_whatsapp_message
        }

    def can_handle(self, command):
        return False # This plugin is intent-based

    def handle(self, command, assistant):
        pass

    def send_whatsapp_message(self, args, assistant):
        """
        Sends a WhatsApp message to a contact using GUI automation.
        """
        contact = args.get("contact")
        message = args.get("message")

        if not all([contact, message]):
            assistant.speak("I'm sorry, I'm missing some information. Please tell me the contact and the message.", is_error=True)
            return

        assistant.speak(f"Okay, sending a WhatsApp message to {contact}.")

        # --- GUI Automation Steps ---
        import pyautogui
        # 1. Bring WhatsApp to the front
        if not window_manager.bring_window_to_front("WhatsApp"):
            assistant.speak("I couldn't find the WhatsApp window. Please make sure it's open.", is_error=True)
            return

        time.sleep(1)

        # 2. Search for the contact
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.write(contact)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)

        # 3. Type and send the message
        pyautogui.write(message)
        pyautogui.press('enter')

        assistant.speak("The message has been sent.")
