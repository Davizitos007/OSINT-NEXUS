import json
import os
from typing import Dict, Any

class ConfigManager:
    """
    Manages application configuration and settings.
    Persists settings to a JSON file in the user's home directory or local folder.
    """
    
    DEFAULT_SETTINGS = {
        "api_keys": {
            "shodan": "",
            "virustotal": "",
            "hunter_io": "",
            "opencage": "",
            "numverify": "",
            "google_api": "",
            "google_cse_id": "",
            "gemini": "",
            "haveibeenpwned": ""
        },
        "scan": {
            "timeout": 30,
            "max_threads": 10,
            "depth": 2
        },
        "ui": {
            "theme": "dark",
            "show_grid": True
        },
        "ai": {
            "enabled": True,
            "model": "gemini-1.5-flash",
            "auto_analyze": True
        }
    }
    
    def __init__(self, filename: str = "settings.json"):
        self.filename = filename
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.load()
        
    def load(self):
        """Load settings from file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    loaded = json.load(f)
                    self._update_recursive(self._settings, loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")
                
    def save(self):
        """Save settings to file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def get(self, section: str, key: str = None) -> Any:
        """Get a setting value."""
        if section not in self._settings:
            return None
        if key is None:
            return self._settings[section]
        return self._settings[section].get(key)
        
    def set(self, section: str, key: str, value: Any):
        """Set a setting value."""
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value
        self.save()
        
    def _update_recursive(self, target: Dict, source: Dict):
        """Update dictionary recursively."""
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._update_recursive(target[k], v)
            else:
                target[k] = v

# Global instance
config = ConfigManager()
