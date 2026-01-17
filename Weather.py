# version="1.2.0"
# author="Rog294super"
# copyright="2026@ Rog294super"
# license="MIT"
# description="A weather application with multi-location support using Tkinter and open-meteo API"

import requests
import time
import threading
import logging
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import os
import sys
import subprocess
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from weather_cache import WeatherCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_REPO = "Rog294super/Weather-App"
VERSION = "1.2.0"
CONFIG_FILE = "weather_locations.json"

# Map waarin het script of de .exe zich bevindt
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(script_dir, CONFIG_FILE)

# Weather code descriptions
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}


class LocationManager:
    """Manages saved locations"""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.locations = self.load_locations()
    
    def load_locations(self):
        """Load saved locations from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('locations', [])
            return []
        except Exception as e:
            logger.error(f"Error loading locations: {e}")
            return []
    
    def save_locations(self):
        """Save locations to config file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({'locations': self.locations}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving locations: {e}")
    
    def add_location(self, name, lat, lon, address, local_name=None):
        """Add a new location"""
        location = {
            'name': name,
            'local_name': local_name or name,
            'lat': lat,
            'lon': lon,
            'address': address,
            'added': datetime.now().isoformat()
        }
        # Check if location already exists
        for loc in self.locations:
            if loc['name'] == name:
                return False
        self.locations.append(location)
        self.save_locations()
        return True
    
    def remove_location(self, name):
        """Remove a location"""
        self.locations = [loc for loc in self.locations if loc['name'] != name]
        self.save_locations()
    
    def get_locations(self):
        """Get all locations"""
        return self.locations


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
                return None
            
            if latest_version > self.current_version:
                return {
                    "version": latest_version,
                    "url": data.get("html_url"),
                    "notes": data.get("body", "No release notes available"),
                    "assets": data.get("assets", [])
                }
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    def download_and_install_update(self, update_info, progress_callback=None):
        """Download and install the update using the updater.exe"""
        try:
            exe_asset = None
            for asset in update_info["assets"]:
                if asset["name"].lower() == "weather.exe":
                    exe_asset = asset
                    break
            
            if not exe_asset:
                raise Exception("No executable found in release assets")
            
            download_url = exe_asset["browser_download_url"]
            exe_path = Path(self.script_dir) / "Weather.exe"
            updater_path = Path(self.script_dir) / "updater.exe"
            
            if not updater_path.exists():
                raise Exception("Updater not found. Please reinstall the application.")
            
            if progress_callback:
                progress_callback("Starting update process...")
            
            subprocess.Popen([str(updater_path), download_url, str(exe_path)], cwd=self.script_dir)
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Error installing update: {e}")
            raise


class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Weather Application v{VERSION}")
        
        # Initialize managers
        self.location_manager = LocationManager(CONFIG_PATH)
        self.update_manager = UpdateManager(VERSION, GITHUB_REPO)
        self.weather_cache = WeatherCache(15)  # 15 minute cache
        
        # Initialize geocoder (lazy loading - only when needed)
        self.geolocator = None
        
        # Memory management - track active threads
        self.active_threads = []

        # Set window icon
        self.set_window_icon()

        # Window sizing
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        windows_width = min(900, screen_width)
        windows_height = min(600, screen_height)
        
        # Center window
        x = (screen_width - windows_width) // 2
        y = (screen_height - windows_height) // 2
        self.root.geometry(f"{windows_width}x{windows_height}+{x}+{y}")
        self.root.minsize(700, 500)
        self.root.resizable(True, True)

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale = max(0.8, min(1.4, screen_width / 1920))

        # Colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#4a90e2"
        self.success_color = "#28a745"

        # Create GUI
        self.create_gui()
        
        # Check for updates on startup (delayed to not slow down startup)
        self.root.after(3000, lambda: self._start_thread(self.check_updates_startup))

    def create_gui(self):
        """Create the main GUI elements"""
        # Main container with two panes
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.bg_color, 
                                     sashwidth=5, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Saved locations
        left_frame = tk.Frame(main_paned, bg=self.bg_color, width=250)
        self.create_locations_panel(left_frame)
        main_paned.add(left_frame, minsize=200)
        
        # Right panel - Weather display
        right_frame = tk.Frame(main_paned, bg=self.bg_color)
        self.create_weather_panel(right_frame)
        main_paned.add(right_frame, minsize=400)

    def _start_thread(self, target, args=()):
        """Start a managed thread with cleanup"""
        # Clean up dead threads every 10 launches
        if len(self.active_threads) > 10:
            self.active_threads = [t for t in self.active_threads if t.is_alive()]
        
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()
        self.active_threads.append(thread)
        return thread

    def create_locations_panel(self, parent):
        """Create the saved locations panel"""
        # Header
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title = tk.Label(header_frame, text="📍 Locations", bg=self.bg_color, 
                        fg=self.fg_color, font=("Arial", 14, "bold"))
        title.pack(side=tk.LEFT)
        
        # Update button
        self.update_button = tk.Button(
            header_frame, text="🔄", bg="#3a3a3a", fg=self.fg_color,
            font=("Arial", 10), command=self.check_updates_manual,
            cursor="hand2", relief=tk.FLAT, width=3
        )
        self.update_button.pack(side=tk.RIGHT)
        
        # Locations list
        list_frame = tk.Frame(parent, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for locations
        self.locations_listbox = tk.Listbox(
            list_frame, bg="#1e1e1e", fg=self.fg_color,
            font=("Arial", 11), selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set, relief=tk.FLAT,
            highlightthickness=0, selectbackground=self.accent_color
        )
        self.locations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.locations_listbox.yview)
        
        # Bind selection event
        self.locations_listbox.bind('<<ListboxSelect>>', self.on_location_select)
        
        # Buttons under list of locations
        # Buttons frame
        btn_frame = tk.Frame(parent, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        remove_btn = tk.Button(
            btn_frame, text="🗑️ Remove", bg="#dc3545", fg=self.fg_color,
            font=("Arial", 9), command=self.remove_selected_location,
            cursor="hand2", relief=tk.FLAT
        )
        remove_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Clear cache button
        clear_cache_btn = tk.Button(
            btn_frame, text="🔄 Clear Cache", bg="#6c757d", fg=self.fg_color,
            font=("Arial", 9), command=self.clear_cache,
            cursor="hand2", relief=tk.FLAT
        )
        clear_cache_btn.pack(fill=tk.X)
        
        # Load saved locations
        self.refresh_locations_list()

    def create_weather_panel(self, parent):
        """Create the weather display panel"""
        # Header with title and version
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            header_frame, text="Weather Forecast", bg=self.bg_color,
            fg=self.fg_color, font=("Arial", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        version_label = tk.Label(
            header_frame, text=f"v{VERSION}", bg=self.bg_color,
            fg="#888888", font=("Arial", 9)
        )
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Cache indicator
        self.cache_label = tk.Label(
            header_frame, text="📦 Cache: 0", bg=self.bg_color,
            fg="#888888", font=("Arial", 8)
        )
        self.cache_label.pack(side=tk.RIGHT)

        # Input frame
        input_frame = tk.Frame(parent, bg=self.bg_color)
        input_frame.pack(pady=10, padx=10, fill=tk.X)

        self.city_entry = tk.Entry(
            input_frame, font=("Arial", 12), width=30
        )
        self.city_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.city_entry.insert(0, "Groningen, Netherlands")
        self.city_entry.bind('<Return>', lambda e: self.fetch_weather_threaded())

        # Fetch button
        fetch_btn = tk.Button(
            input_frame, text="Get Weather", bg=self.accent_color,
            fg=self.fg_color, font=("Arial", 11), command=self.fetch_weather_threaded,
            cursor="hand2", relief=tk.FLAT, padx=15, pady=5
        )
        fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # Add to saved button
        save_btn = tk.Button(
            input_frame, text="💾 Save", bg=self.success_color,
            fg=self.fg_color, font=("Arial", 11), command=self.save_current_location,
            cursor="hand2", relief=tk.FLAT, padx=10, pady=5
        )
        save_btn.pack(side=tk.LEFT)

        # Weather display
        display_frame = tk.Frame(parent, bg=self.bg_color)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.weather_text = scrolledtext.ScrolledText(
            display_frame, wrap=tk.WORD, font=("Courier New", 10),
            bg="#1e1e1e", fg=self.fg_color, relief=tk.FLAT,
            padx=15, pady=15
        )
        self.weather_text.pack(fill=tk.BOTH, expand=True)
        self.weather_text.insert(tk.END, "🌤️  Weather Application v" + VERSION + "\n\n")
        self.weather_text.insert(tk.END, "• Enter a city name and click 'Get Weather'\n")
        self.weather_text.insert(tk.END, "• Click '💾 Save' to add to your locations\n")
        self.weather_text.insert(tk.END, "• Select a saved location to view its weather\n")
        self.weather_text.insert(tk.END, "• 📦 Weather cached for 15 min (faster access!)\n")
        self.weather_text.insert(tk.END, "• To check for updates for the Weather app, click the '🔄' button\n")
        self.weather_text.config(state=tk.DISABLED)
        
        # Store current location data
        self.current_location_data = None

    def update_cache_indicator(self):
        """Update the cache statistics display"""
        stats = self.weather_cache.get_stats()
        self.cache_label.config(text=f"📦 Cache: {stats['entries']}")

    def clear_cache(self):
        """Clear the weather cache"""
        count = self.weather_cache.clear()
        self.update_cache_indicator()
        messagebox.showinfo("Cache Cleared", f"Cleared {count} cached entries.\nNext requests will fetch fresh data.")

    def refresh_locations_list(self):
        """Refresh the locations listbox"""
        self.locations_listbox.delete(0, tk.END)
        locations = self.location_manager.get_locations()
        for loc in locations:
            display_name = f"{loc['local_name']}"
            if loc['local_name'] != loc['name']:
                display_name += f" ({loc['name']})"
            self.locations_listbox.insert(tk.END, display_name)

    def on_location_select(self, event):
        """Handle location selection"""
        selection = self.locations_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        locations = self.location_manager.get_locations()
        if idx >= len(locations):
            return
        
        location = locations[idx]
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, location['name'])
        
        # Fetch weather for this location
        self._start_thread(self.fetch_weather_for_saved_location, (location,))

    def fetch_weather_for_saved_location(self, location):
        """Fetch weather for a saved location"""
        try:
            # Check cache first
            cached = self.weather_cache.get(location['lat'], location['lon'])
            
            if cached:
                # Use cached data - instant!
                self._display_cached_weather(location, cached)
                return
            
            # Not in cache - fetch new
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(tk.END, f"⏳ Loading weather for {location['local_name']}...\n")
            self.weather_text.config(state=tk.DISABLED)
            
            weather_data = self.fetch_weather_data(location['lat'], location['lon'])
            
            # Store current location
            self.current_location_data = {
                'name': location['name'],
                'local_name': location['local_name'],
                'lat': location['lat'],
                'lon': location['lon'],
                'address': location['address']
            }
            
            formatted = self.format_weather_data(weather_data, location['local_name'], 
                                                 location['address'], location['name'])
            
            # Cache it
            self.weather_cache.set(location['lat'], location['lon'], weather_data, formatted)
            self.root.after(0, self.update_cache_indicator)
            
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(tk.END, formatted)
            self.weather_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error fetching saved location weather: {e}")
            self.show_error(str(e))

    def _display_cached_weather(self, location, cached_data):
        """Display cached weather with age info"""
        self.current_location_data = {
            'name': location['name'],
            'local_name': location['local_name'],
            'lat': location['lat'],
            'lon': location['lon'],
            'address': location['address']
        }
        
        age = datetime.now() - cached_data['timestamp']
        age_min = int(age.total_seconds() / 60)
        next_update = 15 - age_min
        
        formatted = cached_data['formatted']
        cache_info = f"\n💾 Cached ({age_min} min old) • Fresh in {next_update} min\n"
        
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete(1.0, tk.END)
        self.weather_text.insert(tk.END, formatted + cache_info)
        self.weather_text.config(state=tk.DISABLED)
        
        self.root.after(0, self.update_cache_indicator)

    def save_current_location(self):
        """Save the currently displayed location"""
        if not self.current_location_data:
            messagebox.showwarning("No Location", "Please fetch weather for a location first.")
            return
        
        success = self.location_manager.add_location(
            self.current_location_data['name'],
            self.current_location_data['lat'],
            self.current_location_data['lon'],
            self.current_location_data['address'],
            self.current_location_data.get('local_name')
        )
        
        if success:
            self.refresh_locations_list()
            messagebox.showinfo("Success", f"Location '{self.current_location_data['local_name']}' saved!")
        else:
            messagebox.showinfo("Already Saved", "This location is already in your list.")

    def remove_selected_location(self):
        """Remove the selected location"""
        selection = self.locations_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a location to remove.")
            return
        
        idx = selection[0]
        locations = self.location_manager.get_locations()
        if idx >= len(locations):
            return
        
        location = locations[idx]
        result = messagebox.askyesno("Confirm", f"Remove '{location['local_name']}'?")
        
        if result:
            self.location_manager.remove_location(location['name'])
            self.refresh_locations_list()

    def get_coordinates(self, location_name):
        """Get coordinates and location names in multiple languages"""
        # Lazy initialize geocoder
        if not self.geolocator:
            try:
                self.geolocator = Nominatim(user_agent=f"weather_app_v{VERSION}")
            except Exception as e:
                raise RuntimeError(f"Geocoding service not available: {e}")
        
        try:
            logger.info(f"Geocoding location: {location_name}")
            location = self.geolocator.geocode(location_name, timeout=10, language='en')
            
            if location:
                # Try to get local name
                try:
                    local_location = self.geolocator.geocode(location_name, timeout=10, 
                                                            language='local', addressdetails=True)
                    local_name = local_location.address if local_location else location.address
                except:
                    local_name = location.address
                
                logger.info(f"Found: {location.latitude}, {location.longitude}")
                return location.latitude, location.longitude, location.address, local_name
            else:
                raise ValueError(f"Could not find location: {location_name}")
                
        except GeocoderTimedOut:
            raise RuntimeError("Geocoding service timed out. Please try again.")
        except GeocoderServiceError as e:
            raise RuntimeError(f"Geocoding service error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to get coordinates: {e}")

    def fetch_weather_data(self, lat, lon):
        """Fetch weather data from Open-Meteo API"""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"precipitation,rain,weather_code,cloud_cover,"
                f"wind_speed_10m,wind_direction_10m"
                f"&timezone=auto"
            )
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise RuntimeError("Weather API request timed out.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Failed to connect to weather service.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch weather data: {e}")

    def format_weather_data(self, weather_data, location_name, address_en, address_local=None):
        """Format weather data for display with proper alignment"""
        try:
            current = weather_data.get('current', {})
            
            temp = current.get('temperature_2m', 'N/A')
            feels_like = current.get('apparent_temperature', 'N/A')
            humidity = current.get('relative_humidity_2m', 'N/A')
            weather_code = current.get('weather_code', 0)
            weather_desc = WEATHER_CODES.get(weather_code, "Unknown")
            wind_speed = current.get('wind_speed_10m', 'N/A')
            wind_direction = current.get('wind_direction_10m', 'N/A')
            precipitation = current.get('precipitation', 0)
            cloud_cover = current.get('cloud_cover', 'N/A')
            
            weather_icon = self.get_weather_icon(weather_code)
            
            # Format with proper alignment
            output = "=" * 64 + "\n"
            output += f"  WEATHER REPORT: {location_name.upper()}\n"
            output += "=" * 64 + "\n\n"
            
            # Show both language versions if different
            if address_local and address_local != address_en:
                output += f"📍 Location (Local): {address_local}\n"
                output += f"📍 Location (EN):    {address_en}\n"
            else:
                output += f"📍 Location: {address_en}\n"
            
            output += f"🕐 Time:     {current.get('time', 'N/A')}\n\n"
            output += "─" * 64 + "\n"
            output += "  CURRENT CONDITIONS\n"
            output += "─" * 64 + "\n\n"
            output += f"{weather_icon}  {weather_desc}\n\n"
            
            # Aligned data - no emojis on data lines for perfect alignment
            output += f"Temperature:        {str(temp):>6}°C\n"
            output += f"Feels Like:         {str(feels_like):>6}°C\n"
            output += f"Humidity:           {str(humidity):>6}%\n"
            output += f"Wind Speed:         {str(wind_speed):>6} km/h\n"
            output += f"Wind Direction:     {str(wind_direction):>6}°\n"
            output += f"Precipitation:      {str(precipitation):>6} mm\n"
            output += f"Cloud Cover:        {str(cloud_cover):>6}%\n"
            output += "\n" + "=" * 64 + "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return f"Error formatting weather data: {e}"

    def get_weather_icon(self, code):
        """Get emoji icon for weather code"""
        icons = {
            0: "☀️", 1: "🌤️", 2: "🌤️", 3: "☁️",
            45: "🌫️", 48: "🌫️",
            51: "🌧️", 53: "🌧️", 55: "🌧️",
            61: "🌧️", 63: "🌧️", 65: "⛈️",
            71: "🌨️", 73: "🌨️", 75: "🌨️", 77: "🌨️",
            80: "🌧️", 81: "🌧️", 82: "⛈️",
            85: "🌨️", 86: "🌨️",
            95: "⚡", 96: "⚡", 99: "⚡"
        }
        return icons.get(code, "🌈")

    def fetch_weather_threaded(self):
        """Fetch weather in a separate thread"""
        self._start_thread(self.fetch_weather)

    def fetch_weather(self):
        """Main method to fetch and display weather"""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return
        
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete(1.0, tk.END)
        self.weather_text.insert(tk.END, f"⏳ Fetching weather for {city}...\n")
        self.weather_text.config(state=tk.DISABLED)
        
        try:
            lat, lon, address_en, address_local = self.get_coordinates(city)
            
            # Check cache first
            cached = self.weather_cache.get(lat, lon)
            if cached:
                self.current_location_data = {
                    'name': city,
                    'local_name': address_local,
                    'lat': lat,
                    'lon': lon,
                    'address': address_en
                }
                age = datetime.now() - cached['timestamp']
                age_min = int(age.total_seconds() / 60)
                cache_info = f"\n💾 Cached ({age_min} min old) • Fresh in {15-age_min} min\n"
                
                self.weather_text.config(state=tk.NORMAL)
                self.weather_text.delete(1.0, tk.END)
                self.weather_text.insert(tk.END, cached['formatted'] + cache_info)
                self.weather_text.config(state=tk.DISABLED)
                self.update_cache_indicator()
                return
            
            # Fetch new data
            weather_data = self.fetch_weather_data(lat, lon)
            
            # Store current location
            self.current_location_data = {
                'name': city,
                'local_name': address_local,
                'lat': lat,
                'lon': lon,
                'address': address_en
            }
            
            formatted = self.format_weather_data(weather_data, city, address_en, address_local)
            
            # Cache it
            self.weather_cache.set(lat, lon, weather_data, formatted)
            self.update_cache_indicator()
            
            self.weather_text.config(state=tk.NORMAL)
            self.weather_text.delete(1.0, tk.END)
            self.weather_text.insert(tk.END, formatted)
            self.weather_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error in fetch_weather: {e}")
            self.show_error(str(e))

    def show_error(self, error_msg):
        """Display error message"""
        self.weather_text.config(state=tk.NORMAL)
        self.weather_text.delete(1.0, tk.END)
        self.weather_text.insert(tk.END, "❌ ERROR\n\n")
        self.weather_text.insert(tk.END, f"{error_msg}\n\n")
        self.weather_text.insert(tk.END, "Please check:\n")
        self.weather_text.insert(tk.END, "  • City name spelling\n")
        self.weather_text.insert(tk.END, "  • Internet connection\n")
        self.weather_text.insert(tk.END, "  • Try format: 'City, Country'\n")
        self.weather_text.config(state=tk.DISABLED)

    def check_updates_startup(self):
        """Check for updates on startup (silent)"""
        try:
            time.sleep(2)
            update_info = self.update_manager.check_for_updates()
            if update_info:
                self.root.after(0, lambda: self.update_button.config(
                    text=f"⬇️", bg=self.success_color
                ))
        except Exception as e:
            logger.error(f"Error checking updates: {e}")

    def check_updates_manual(self):
        """Check for updates manually"""
        self.update_button.config(state=tk.DISABLED)
        
        def check_thread():
            try:
                update_info = self.update_manager.check_for_updates()
                if update_info:
                    self.root.after(0, lambda: self.show_update_dialog(update_info))
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Up to Date", f"You are running the latest version (v{VERSION})"
                    ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Check Failed", f"Failed to check for updates:\n{str(e)}"
                ))
            finally:
                self.root.after(0, lambda: self.update_button.config(state=tk.NORMAL))
        
        threading.Thread(target=check_thread, daemon=True).start()

    def show_update_dialog(self, update_info):
        """Show update dialog"""
        message = f"New version available: v{update_info['version']}\n\n"
        message += f"Current: v{VERSION}\n\nInstall now?"
        
        if messagebox.askyesno("Update Available", message):
            self.install_update(update_info)

    def install_update(self, update_info):
        """Install update"""
        try:
            self.update_manager.download_and_install_update(update_info)
            time.sleep(0.5)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Update Failed", f"Failed to install update:\n{str(e)}")

    def set_window_icon(self):
        """Set window icon if available"""
        try:
            icon_path = os.path.join(script_dir, "Weather_icon.ico")
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