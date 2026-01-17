"""
Weather Cache Module
Caches weather data to reduce API calls and improve performance
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_DURATION_MINUTES = 15  # Weather data updates every 15 minutes


class WeatherCache:
    """Caches weather data to reduce API calls and improve performance"""
    
    def __init__(self, cache_duration_minutes=15):
        self.cache = {}  # {location_key: {'data': dict, 'formatted': str, 'timestamp': datetime}}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        logger.info(f"WeatherCache initialized ({cache_duration_minutes} min duration)")
    
    def get_cache_key(self, lat, lon):
        """Generate cache key from coordinates (rounded to 3 decimals ~100m accuracy)"""
        return f"{round(lat, 3)}_{round(lon, 3)}"
    
    def get(self, lat, lon):
        """Get cached weather data if still valid"""
        key = self.get_cache_key(lat, lon)
        
        if key in self.cache:
            cached = self.cache[key]
            age = datetime.now() - cached['timestamp']
            
            if age < self.cache_duration:
                logger.info(f"Cache HIT for {key} (age: {int(age.total_seconds())}s)")
                return cached
            else:
                logger.info(f"Cache EXPIRED for {key} (age: {int(age.total_seconds())}s)")
                del self.cache[key]  # Remove expired entry to free memory
        
        logger.info(f"Cache MISS for {key}")
        return None
    
    def set(self, lat, lon, weather_data, formatted_text):
        """Cache weather data"""
        key = self.get_cache_key(lat, lon)
        self.cache[key] = {
            'data': weather_data,
            'formatted': formatted_text,
            'timestamp': datetime.now()
        }
        logger.info(f"Cached weather for {key} (total cached: {len(self.cache)})")
    
    def clear(self):
        """Clear all cached data"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def get_stats(self):
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'keys': list(self.cache.keys())
        }
