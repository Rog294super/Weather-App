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
import subprocess
import json
from pathlib import Path
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
GITHUB_REPO = "Rog294super/Weather-App"
VERSION = "1.0.0"
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


class UpdateManager:
    """Manages application updates from GitHub releases"""
    
    def __init__(self, current_version, github_repo):
        self.current_version = current_version
        self.github_repo = github_repo
        self.script_dir = script_dir
        
    def check_for_updates(self):
        """Check if a new version is available"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to check for updates: HTTP {response.status_code}")
                return None
            
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                logger.warning("No version tag found in release")
                return None
            
            logger.info(f"Current version: {self.current_version}, Latest version: {latest_version}")
            
            # Compare versions (simple string comparison for now)
            if latest_version > self.current_version:
                return {
                    "version": latest_version,
                    "url": data.get("html_url"),
                    "notes": data.get("body", "No release notes available"),
                    "assets": data.get("assets", [])
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking for updates: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking updates: {e}")
            return None
    
    def download_and_install_update(self, update_info, progress_callback=None):
        """Download and install the update using the updater.exe"""
        try:
            # Find the main executable asset
            exe_asset = None
            updater_asset = None
            
            for asset in update_info["assets"]:
                name = asset["name"].lower()
                if name == "weather.exe":
                    exe_asset = asset
                elif "updater" in name and name.endswith(".exe"):
                    updater_asset = asset
            
            if not exe_asset:
                raise Exception("No executable found in release assets")
            
            download_url = exe_asset["browser_download_url"]
            exe_path = Path(self.script_dir) / "Weather.exe"
            
            # Check if updater exists
            updater_path = Path(self.script_dir) / "updater.exe"
            
            if not updater_path.exists() and updater_asset:
                # Download updater first
                if progress_callback:
                    progress_callback("Downloading updater...")
                
                logger.info("Downloading updater...")
                response = requests.get(updater_asset["browser_download_url"], timeout=30)
                response.raise_for_status()
                
                with open(updater_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info("Updater downloaded successfully")
            
            if not updater_path.exists():
                raise Exception("Updater not found. Please reinstall the application.")
            
            # Start the updater process
            if progress_callback:
                progress_callback("Starting update process...")
            
            logger.info(f"Launching updater: {updater_path}")
            logger.info(f"Download URL: {download_url}")
            logger.info(f"Target path: {exe_path}")
            
            # Launch updater with arguments
            subprocess.Popen([
                str(updater_path),
                download_url,
                str(exe_path)
            ], cwd=self.script_dir)
            
            # Give the updater time to start
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing update: {e}")
            raise


class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Weather Application v{VERSION}")
        self.debug_log_path = os.path.join(script_dir, "weather_debug.log")
        
        # Initialize update manager
        self.update_manager = UpdateManager(VERSION, GITHUB_REPO)
        
        # Initialize geocoder
        try:
            self.geolocator = Nominatim(user_agent=f"weather_app_v{VERSION}")
        except Exception as e:
            logger.error(f"Failed to initialize geocoder: {e}")
            messagebox.showerror("Initialization Error", "Failed to initialize geocoding service")
            self.geolocator = None

        # Icon application
        self.set_window_icon()

        # Window sizing
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        windows_width = min(700, screen_width)
        windows_height = min(550, screen_height)
        
        # Center window
        x = (screen_width - windows_width) // 2
        y = (screen_height - windows_height) // 2
        self.root.geometry(f"{windows_width}x{windows_height}+{x}+{y}")
        self.root.minsize(500, 450)
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
        self.success_color = "#28a745"
        self.warning_color = "#ffc107"

        # Create GUI
        self.create_gui()
        
        # Check for updates on startup (in background)
        threading.Thread(target=self.check_updates_startup, daemon=True).start()

    def create_gui(self):
        """Create the main GUI elements"""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header frame with title and update button
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Weather Forecast", 
            bg=self.bg_color, 
            fg=self.fg_color, 
            font=("Arial", int(18 * self.scale), "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Version label
        version_label = tk.Label(
            header_frame,
            text=f"v{VERSION}",
            bg=self.bg_color,
            fg="#888888",
            font=("Arial", int(9 * self.scale))
        )
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Update button
        self.update_button = tk.Button(
            header_frame,
            text="🔄 Check Updates",
            bg="#3a3a3a",
            fg=self.fg_color,
            font=("Arial", int(9 * self.scale)),
            command=self.check_updates_manual,
            cursor="hand2",
            relief=tk.FLAT,
            padx=10,
            pady=2
        )
        self.update_button.pack(side=tk.RIGHT)

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
        
        # Bind Enter key to fetch weather
        self.city_entry.bind('<Return>', lambda e: self.fetch_weather_threaded())

        # Fetch button
        fetch_button = tk.Button(
            main_frame, 
            text="Fetch Weather", 
            bg=self.accent_color, 
            fg=self.fg_color, 
            font=("Arial", int(12 * self.scale)),
            command=self.fetch_weather_threaded,
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        fetch_button.pack(pady=10)

        # Weather display frame
        self.weather_frame = tk.Frame(main_frame, bg=self.bg_color)
        self.weather_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Scrolled text for weather info
        self.weather_text = scrolledtext.ScrolledText(
            self.weather_frame,
            wrap=tk.WORD,
            width=60,
            height=15,
            font=("Consolas", int(10 * self.scale)),
            bg="#1e1e1e",
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.weather_text.pack(fill=tk.BOTH, expand=True)
        self.weather_text.insert(tk.END, "🌤️  Weather Application\n\n")
        self.weather_text.insert(tk.END, "Enter a city name and click 'Fetch Weather' to get started.\n")
        self.weather_text.insert(tk.END, "You can also press Enter after typing the city name.\n")
        self.weather_text.config(state=tk.DISABLED)

    def check_updates_startup(self):
        """Check for updates on startup (silent)"""
        try:
            time.sleep(2)  # Wait a bit after startup
            update_info = self.update_manager.check_for_updates()
            
            if update_info:
                # Update the button to indicate update available
                self.root.after(0, lambda: self.update_button.config(
                    text=f"⬇️ Update Available (v{update_info['version']})",
                    bg=self.success_color
                ))
        except Exception as e:
            logger.error(f"Error checking updates on startup: {e}")

    def check_updates_manual(self):
        """Check for updates manually (with user feedback)"""
        self.update_button.config(state=tk.DISABLED, text="Checking...")
        
        def check_thread():
            try:
                update_info = self.update_manager.check_for_updates()
                
                if update_info:
                    self.root.after(0, lambda: self.show_update_dialog(update_info))
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Up to Date",
                        f"You are running the latest version (v{VERSION})"
                    ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Check Failed",
                    f"Failed to check for updates:\n{str(e)}"
                ))
            finally:
                self.root.after(0, lambda: self.update_button.config(
                    state=tk.NORMAL,
                    text="🔄 Check Updates"
                ))
        
        threading.Thread(target=check_thread, daemon=True).start()

    def show_update_dialog(self, update_info):
        """Show dialog with update information"""
        message = f"A new version is available!\n\n"
        message += f"Current version: v{VERSION}\n"
        message += f"Latest version: v{update_info['version']}\n\n"
        message += f"Release notes:\n{update_info['notes'][:200]}"
        
        if len(update_info['notes']) > 200:
            message += "..."
        
        message += "\n\nDo you want to download and install the update?\n"
        message += "(The application will close and restart after update)"
        
        result = messagebox.askyesno("Update Available", message)
        
        if result:
            self.install_update(update_info)

    def install_update(self, update_info):
        """Install the update"""
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Installing Update")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the window
        progress_window.update_idletasks()
        x = (self.screen_width - 400) // 2
        y = (self.screen_height - 150) // 2
        progress_window.geometry(f"+{x}+{y}")
        
        progress_frame = tk.Frame(progress_window, bg=self.bg_color)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        status_label = tk.Label(
            progress_frame,
            text="Preparing update...",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 11)
        )
        status_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=300
        )
        progress_bar.pack(pady=10)
        progress_bar.start(10)
        
        def progress_callback(message):
            status_label.config(text=message)
            progress_window.update()
        
        def update_thread():
            try:
                success = self.update_manager.download_and_install_update(
                    update_info,
                    progress_callback
                )
                
                if success:
                    progress_window.after(0, progress_window.destroy)
                    time.sleep(0.5)
                    # Close the application - updater will restart it
                    self.root.after(0, self.root.destroy)
                else:
                    raise Exception("Update installation failed")
                    
            except Exception as e:
                logger.error(f"Update installation error: {e}")
                progress_window.after(0, progress_window.destroy)
                messagebox.showerror(
                    "Update Failed",
                    f"Failed to install update:\n{str(e)}\n\nPlease try again or download manually."
                )
        
        threading.Thread(target=update_thread, daemon=True).start()

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
            output = "=" * 60 + "\n"
            output += f"  WEATHER REPORT: {location_name.upper()}\n"
            output += "=" * 60 + "\n\n"
            output += f"📍 Location: {address}\n"
            output += f"🕐 Time: {current.get('time', 'N/A')}\n\n"
            output += "─" * 60 + "\n"
            output += "  CURRENT CONDITIONS\n"
            output += "─" * 60 + "\n\n"
            
            # Weather icon
            weather_icon = self.get_weather_icon(weather_code)
            output += f"{weather_icon} {weather_desc}\n\n"
            
            output += f"🌡️  Temperature:        {temp}°C\n"
            output += f"🤚 Feels Like:         {feels_like}°C\n"
            output += f"💧 Humidity:           {humidity}%\n"
            output += f"💨 Wind Speed:         {wind_speed} km/h\n"
            output += f"🧭 Wind Direction:     {wind_direction}°\n"
            output += f"🌧️  Precipitation:      {precipitation} mm\n"
            output += f"☁️  Cloud Cover:        {cloud_cover}%\n"
            output += "\n" + "=" * 60 + "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return f"Error formatting weather data: {e}"

    def get_weather_icon(self, code):
        """Get emoji icon for weather code"""
        if code == 0:
            return "☀️"
        elif code in [1, 2]:
            return "🌤️"
        elif code == 3:
            return "☁️"
        elif code in [45, 48]:
            return "🌫️"
        elif code in [51, 53, 55, 61, 63, 80, 81]:
            return "🌧️"
        elif code in [65, 82]:
            return "⛈️"
        elif code in [71, 73, 75, 77, 85, 86]:
            return "🌨️"
        elif code in [95, 96, 99]:
            return "⚡"
        return "🌈"

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
        self.weather_text.insert(tk.END, "⏳ Fetching weather data...\n")
        self.weather_text.insert(tk.END, f"   Looking up: {city}\n")
        self.weather_text.config(state=tk.DISABLED)
        
        try:
            # Get coordinates
            lat, lon, address = self.get_coordinates(city)
            
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.insert(tk.END, f"✓ Coordinates found: {lat:.4f}, {lon:.4f}\n")
            self.weather_text.insert(tk.END, "⏳ Fetching weather...\n")
            self.weather_text.config(state=tk.DISABLED)
            
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
            self.weather_text.insert(tk.END, "❌ ERROR\n\n")
            self.weather_text.insert(tk.END, f"{str(e)}\n\n")
            self.weather_text.insert(tk.END, "Please check:\n")
            self.weather_text.insert(tk.END, "  • City name spelling\n")
            self.weather_text.insert(tk.END, "  • Internet connection\n")
            self.weather_text.insert(tk.END, "  • Try format: 'City, Country'\n")
            self.weather_text.config(state=tk.DISABLED)

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
