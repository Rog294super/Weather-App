# version="1.0.0"
# author="Rog294super"
# copyright="2026@ Rog294super"
# license="MIT"
# description="A simple weather application using Tkinter and open-meteo API"

# import necessary modules
import requests
import time
import threading
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import file_handler as fh
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# variable declarations
Github_Repo = "Rog294super/Weather-App"
Version = "1.0.0"
api_open_meteo = "https://api.open-meteo.com/v1/forecast"
default_params = {
    "latitude": 53.122,
    "longitude": 6.351,
    "current": "temperature_2m,weathercode,windspeed_10m,precipitation"
}

# Map waarin het script of de .exe zich bevindt
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

# Weather code descriptions
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}


class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Application")
        self.debug_log_path = os.path.join(script_dir, "weather_debug.log")
        
        # Initialize geocoder
        try:
            self.geolocator = Nominatim(user_agent="weather_app_v1.0")
        except Exception as e:
            logger.error(f"Failed to initialize geocoder: {e}")
            messagebox.showerror("Initialization Error", "Failed to initialize geocoding service")
            self.geolocator = None

        # Icon application
        self.set_window_icon()

        # Window sizing
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        windows_width = min(600, screen_width)
        windows_height = min(500, screen_height)
        
        # Center window
        x = (screen_width - windows_width) // 2
        y = (screen_height - windows_height) // 2
        self.root.geometry(f"{windows_width}x{windows_height}+{x}+{y}")
        self.root.minsize(400, 400)
        self.root.resizable(True, True)

        # Saving variables
        self.screen_width = screen_width
        self.screen_height = screen_height 
        self.windows_width = windows_width
        self.windows_height = windows_height
        self.scale = max(0.8, min(1.4, screen_width / 1920))

        # Style settings
        style = ttk.Style()
        style.theme_use("clam")

        # Colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#4a90e2"

        # Create GUI
        self.create_gui()

    def create_gui(self):
        """Create the main GUI elements"""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame, 
            text="Weather Forecast", 
            bg=self.bg_color, 
            fg=self.fg_color, 
            font=("Arial", int(18 * self.scale), "bold")
        )
        title_label.pack(pady=(0, 20))

        # Input frame
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(pady=10)

        city_label = tk.Label(
            input_frame, 
            text="City, Country:", 
            bg=self.bg_color, 
            fg=self.fg_color, 
            font=("Arial", int(12 * self.scale))
        )
        city_label.grid(row=0, column=0, padx=5, sticky="w")

        self.city_entry = tk.Entry(
            input_frame, 
            font=("Arial", int(12 * self.scale)),
            width=30
        )
        self.city_entry.grid(row=0, column=1, padx=5)
        self.city_entry.insert(0, "Groningen, Netherlands")

        # Fetch button
        fetch_button = tk.Button(
            main_frame, 
            text="Fetch Weather", 
            bg=self.accent_color, 
            fg=self.fg_color, 
            font=("Arial", int(12 * self.scale)),
            command=self.fetch_weather_threaded,
            cursor="hand2"
        )
        fetch_button.pack(pady=10)

        # Weather display frame
        self.weather_frame = tk.Frame(main_frame, bg=self.bg_color)
        self.weather_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Scrolled text for weather info
        self.weather_text = scrolledtext.ScrolledText(
            self.weather_frame,
            wrap=tk.WORD,
            width=50,
            height=15,
            font=("Arial", int(10 * self.scale)),
            bg="#1e1e1e",
            fg=self.fg_color
        )
        self.weather_text.pack(fill=tk.BOTH, expand=True)
        self.weather_text.insert(tk.END, "Enter a city name and click 'Fetch Weather' to get started.\n")
        self.weather_text.config(state=tk.DISABLED)

    def get_coordinates(self, location_name):
        """Get latitude and longitude from city and country name"""
        if not self.geolocator:
            raise RuntimeError("Geocoding service not available")
        
        try:
            logger.info(f"Geocoding location: {location_name}")
            location = self.geolocator.geocode(location_name, timeout=10)
            
            if location:
                logger.info(f"Found coordinates: {location.latitude}, {location.longitude}")
                return location.latitude, location.longitude, location.address
            else:
                raise ValueError(f"Could not find location: {location_name}")
                
        except GeocoderTimedOut:
            logger.error("Geocoding service timed out")
            raise RuntimeError("Geocoding service timed out. Please try again.")
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error: {e}")
            raise RuntimeError(f"Geocoding service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            raise RuntimeError(f"Failed to get coordinates: {e}")

    def fetch_weather_data(self, lat, lon):
        """Fetch detailed weather data from Open-Meteo API"""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
                f"wind_speed_10m,wind_direction_10m,wind_gusts_10m"
                f"&hourly=temperature_2m,precipitation_probability,precipitation,weather_code"
                f"&forecast_days=1"
                f"&timezone=auto"
            )
            
            logger.info(f"Fetching weather from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Weather data fetched successfully")
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Weather API request timed out")
            raise RuntimeError("Weather API request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to weather API")
            raise RuntimeError("Failed to connect to weather service. Check your internet connection.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise RuntimeError(f"Weather API error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise RuntimeError(f"Failed to fetch weather data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            raise RuntimeError(f"Unexpected error: {e}")

    def format_weather_data(self, weather_data, location_name, address):
        """Format weather data for display"""
        try:
            current = weather_data.get('current', {})
            
            # Extract current weather
            temp = current.get('temperature_2m', 'N/A')
            feels_like = current.get('apparent_temperature', 'N/A')
            humidity = current.get('relative_humidity_2m', 'N/A')
            weather_code = current.get('weather_code', 0)
            weather_desc = WEATHER_CODES.get(weather_code, "Unknown")
            wind_speed = current.get('wind_speed_10m', 'N/A')
            wind_direction = current.get('wind_direction_10m', 'N/A')
            precipitation = current.get('precipitation', 0)
            cloud_cover = current.get('cloud_cover', 'N/A')
            
            # Format output
            output = f"Weather Report for: {location_name}\n"
            output += f"Location: {address}\n"
            output += f"Time: {current.get('time', 'N/A')}\n"
            output += "=" * 60 + "\n\n"
            
            output += f"Current Conditions: {weather_desc}\n"
            output += f"Temperature: {temp}°C\n"
            output += f"Feels Like: {feels_like}°C\n"
            output += f"Humidity: {humidity}%\n"
            output += f"Wind Speed: {wind_speed} km/h\n"
            output += f"Wind Direction: {wind_direction}°\n"
            output += f"Precipitation: {precipitation} mm\n"
            output += f"Cloud Cover: {cloud_cover}%\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return f"Error formatting weather data: {e}"

    def fetch_weather_threaded(self):
        """Fetch weather in a separate thread to avoid UI freezing"""
        thread = threading.Thread(target=self.fetch_weather, daemon=True)
        thread.start()

    def fetch_weather(self):
        """Main method to fetch and display weather"""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return
        
        # Update UI
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete(1.0, tk.END)
        self.weather_text.insert(tk.END, "Fetching weather data...\n")
        self.weather_text.config(state=tk.DISABLED)
        
        try:
            # Get coordinates
            lat, lon, address = self.get_coordinates(city)
            
            # Fetch weather
            weather_data = self.fetch_weather_data(lat, lon)
            
            # Format and display
            formatted_weather = self.format_weather_data(weather_data, city, address)
            
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(tk.END, formatted_weather)
            self.weather_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error in fetch_weather: {e}")
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(tk.END, f"Error: {str(e)}\n\nPlease check:\n")
            self.weather_text.insert(tk.END, "- City name spelling\n")
            self.weather_text.insert(tk.END, "- Internet connection\n")
            self.weather_text.insert(tk.END, "- Try format: 'City, Country'\n")
            self.weather_text.config(state=tk.DISABLED)
            messagebox.showerror("Error", str(e))

    def set_window_icon(self):
        """Set window icon if available"""
        try:
            icon_path = os.path.join(script_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

    def on_closing(self):
        """Handle window closing"""
        logger.info("Application closing")
        self.root.destroy()


def main():
    """Main entry point"""
    try:
        root = tk.Tk()
        app = WeatherAppGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()
