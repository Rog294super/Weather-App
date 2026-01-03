# Weather Application

A Python-based weather application using Tkinter GUI and the Open-Meteo API with integrated auto-update functionality.

## 🌟 Features
- 🌍 City name to coordinates conversion using geopy/Nominatim
- 🌤️ Real-time weather data from Open-Meteo API
- 🔄 Automatic update checking and installation
- 🛡️ Comprehensive error handling
- 🎨 User-friendly GUI with dark theme
- 📊 Detailed weather information display with emoji icons
- ⚡ Fast startup with ONEDIR build
- ⌨️ Enter key support for quick weather lookup

## 📦 Installation

### Option 1: Using the Installer (Recommended)
1. Download `Weather_Installer.exe` from the [latest release](https://github.com/Rog294super/Weather-App/releases/latest)
2. Run the installer
3. Choose installation location
4. Click "Install"
5. The installer will:
   - Download the latest version
   - Create desktop shortcut
   - Set up auto-update functionality

### Option 2: Manual Installation
1. Download `Weather.zip` from the [latest release](https://github.com/Rog294super/Weather-App/releases/latest)
2. Extract to your preferred location
3. Run `Weather.exe`

### Option 3: From Source
1. Clone the repository:
```bash
git clone https://github.com/Rog294super/Weather-App.git
cd Weather-App
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python Weather.py
```

## 🚀 Usage
1. Enter a city name (e.g., "Amsterdam" or "Amsterdam, Netherlands")
2. Click "Fetch Weather" or press Enter
3. View detailed weather information with emoji indicators

## 🔄 Auto-Update System

The application includes a built-in update system:
- **Automatic check**: Checks for updates on startup (background)
- **Manual check**: Click "🔄 Check Updates" button
- **One-click install**: Automatically downloads and installs updates
- **Seamless restart**: Application restarts after update

The update process uses a C++ updater (`updater.exe`) that:
1. Closes the running application
2. Downloads the new version
3. Replaces the old executable
4. Restarts the application

## 🏗️ Building from Source

### Prerequisites
- Python 3.8+
- PyInstaller: `pip install pyinstaller`
- C++ compiler (for updater): MinGW-w64 or Visual Studio

### Build Instructions

1. **Build the application:**
```bash
compiler.bat
```
Choose from:
- Option 1: ONEDIR (Instant Startup) - **Recommended**
- Option 2: Installer
- Option 3: Build both
- Option 4: Clean build folders

2. **Build the updater (if needed):**
```bash
cd Updater
compile_updater.bat
```

The ONEDIR build creates a folder structure with instant startup (<0.5s) instead of a single large executable.

## 📁 Project Structure

```
Weather/
├── Weather.py              # Main application
├── file_handler.py         # File operations utility
├── weather_installer.py    # Online installer
├── Weather.spec           # PyInstaller spec for main app
├── Weather_Installer.spec # PyInstaller spec for installer
├── compiler.bat           # Build automation script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── LICENSE               # MIT License
└── Updater/
    ├── updater_final.cpp     # C++ updater source
    ├── compile_updater.bat   # Updater build script
    └── test_update.bat       # Update testing script
```

## 🛠️ Technical Details

### Weather Data
- **API**: Open-Meteo (free, no API key required)
- **Data includes**: Temperature, humidity, wind, precipitation, cloud cover
- **Weather codes**: Translated to human-readable descriptions with emoji icons

### Geocoding
- **Service**: Nominatim (OpenStreetMap)
- **Features**: City name → coordinates conversion
- **Timeout handling**: 10-second timeout with retry logic

### Error Handling
- ✅ Network timeout handling
- ✅ Invalid location handling
- ✅ API error handling
- ✅ Geocoding service errors
- ✅ Update system errors
- ✅ Comprehensive logging

### Update System Architecture
```
Weather.exe
    ↓ (checks GitHub API)
    ↓ (new version available)
    ↓ (launches)
updater.exe <download_url> <target_path>
    ↓ (closes Weather.exe)
    ↓ (downloads new version)
    ↓ (replaces old executable)
    ↓ (restarts Weather.exe)
```

## 🎯 Key Improvements from v1.0.0

### Integrated Update System
- ✅ Automatic update checking on startup
- ✅ Manual update check button
- ✅ One-click update installation
- ✅ Progress indicators during update
- ✅ Automatic restart after update

### Enhanced UI
- ✅ Version display in header
- ✅ Update button with status indication
- ✅ Better weather formatting with emojis
- ✅ Enter key support
- ✅ Improved error messages

### Better .gitignore
- ✅ Excludes build artifacts
- ✅ Excludes user-specific files
- ✅ Excludes IDE files
- ✅ Keeps source files tracked

### Code Quality
- ✅ UpdateManager class for update logic
- ✅ Better separation of concerns
- ✅ Improved error handling
- ✅ Better logging throughout

## 🐛 Troubleshooting

### Update Issues
- **"Updater not found"**: Reinstall the application using the installer
- **Update fails**: Try manual download from GitHub releases
- **Application doesn't restart**: Manually start Weather.exe

### Weather Fetch Issues
- **"Geocoding service timed out"**: Check internet connection, try again
- **"Could not find location"**: Try adding country name (e.g., "Paris, France")
- **"Weather API error"**: Service may be temporarily unavailable

### General Issues
- **Application won't start**: Check Windows Defender/antivirus settings
- **Slow startup**: Use ONEDIR version from installer
- **Missing icon**: Icon.ico file may be missing (optional, won't affect functionality)

## 📝 Development

### Testing Updates
```bash
cd Updater
test_update.bat
```
This simulates the update process without affecting the live application.

### Creating a Release
1. Update VERSION in Weather.py
2. Build with `compiler.bat` (option 3 - build all)
3. Create GitHub release with tag (e.g., v1.0.1)
4. Upload:
   - `dist/Weather.zip` (manual installation)
   - `dist/Weather_Installer.exe` (auto-installer)
   - `Updater/updater.exe` (required for auto-update)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 👤 Author

**Rog294super**
- GitHub: [@Rog294super](https://github.com/Rog294super)

## 🙏 Acknowledgments

- [Open-Meteo](https://open-meteo.com/) - Free weather API
- [Nominatim](https://nominatim.org/) - Free geocoding service
- [geopy](https://github.com/geopy/geopy) - Geocoding library
- [PyInstaller](https://www.pyinstaller.org/) - Python to executable conversion

## 📊 Version History

### v1.0.0 (Current)
- Initial release
- Basic weather fetching
- City to coordinates conversion
- Dark theme GUI
- Integrated auto-update system
- ONEDIR instant startup build
- Enhanced UI with emojis
- Enter key support
- Update checking and installation
