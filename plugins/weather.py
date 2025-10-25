import requests
from src.plugin_interface import Plugin

class WeatherPlugin(Plugin):
    """
    A plugin to get the weather.
    """
    def can_handle(self, command):
        return "weather in" in command

    def handle(self, command, assistant):
        location = command.split("weather in")[-1].strip()
        api_key = assistant.config.get("weather_api_key")
        if not api_key:
            assistant.speak("I'm sorry, I don't have a weather API key configured. Please add one to your config.json file.")
            return

        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        try:
            response = requests.get(url)
            data = response.json()
            if data["cod"] == 200:
                weather_desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                assistant.speak(f"The weather in {location} is {weather_desc} with a temperature of {temp} degrees Celsius.")
            else:
                assistant.speak(f"I'm sorry, I couldn't get the weather for {location}.")
        except Exception as e:
            assistant.speak(f"I'm sorry, I encountered an error while getting the weather: {e}")
