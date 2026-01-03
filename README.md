# Weather Application

A Python-based weather application using Tkinter GUI and the Open-Meteo API.

## Features
- City name to coordinates conversion using geopy/Nominatim
- Real-time weather data from Open-Meteo API
- Comprehensive error handling
- User-friendly GUI with dark theme
- Detailed weather information display

## Installation

1. Download the Weather_installer.exe or download the whole Weather.zip
Execute the installer and select a location for install or unzip the downloaded weather.zip in a chosen location.
```

2. Run the application:
``` Go to the chosen location and click on the weather.exe.
```

## Usage
1. Enter a city name (optionally with country: "Amsterdam, Netherlands")
2. Click "Fetch Weather"
3. View detailed weather information

## Key Improvements Made

### Error Handling
- **Geocoding errors**: Handles timeouts, service errors, and invalid locations
- **API errors**: Handles connection errors, timeouts, and HTTP errors
- **Input validation**: Checks for empty inputs
- **Logging**: Comprehensive logging for debugging

### Features Added
- **Threading**: Weather fetching doesn't freeze the UI
- **Weather codes**: Human-readable weather descriptions
- **Centered window**: Better user experience
- **Scrolled text widget**: Better for longer weather reports
- **Default city**: Pre-filled with "Groningen, Netherlands"

## API Information
- **Open-Meteo API**: Free weather API, no API key required
- **Nominatim (OpenStreetMap)**: Free geocoding service

## Error Messages
The application provides helpful error messages for:
- Invalid city names
- Network connectivity issues
- API timeouts
- Service unavailability
