import os
from twilio.rest import Client
from src.plugin_interface import Plugin

class PhoneIntegrationPlugin(Plugin):
    """
    A plugin to handle phone integration commands, such as sending SMS messages.
    """
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = None
        if self.account_sid and self.auth_token and self.twilio_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                print(f"Error initializing Twilio client: {e}")

    def get_intent_map(self):
        return {
            "send_sms": self.send_sms
        }

    def can_handle(self, command):
        return False # This plugin is intent-based

    def handle(self, command, assistant):
        pass

    def send_sms(self, args, assistant):
        """
        Sends an SMS message using Twilio.
        """
        if not self.client:
            assistant.speak("I'm sorry, the phone integration is not configured. Please set up your Twilio credentials.", is_error=True)
            return

        to_number = args.get("to_number")
        message = args.get("message")

        if not all([to_number, message]):
            assistant.speak("I'm sorry, I'm missing some information. Please tell me the phone number and the message.", is_error=True)
            return

        try:
            self.client.messages.create(
                to=to_number,
                from_=self.twilio_number,
                body=message
            )
            assistant.speak(f"I've sent the message to {to_number}.")
        except Exception as e:
            assistant.speak(f"I'm sorry, I couldn't send the message. The following error occurred: {e}", is_error=True)
