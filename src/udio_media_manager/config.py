# config.py - Final Fully Upgraded Version

"""
Centralized configuration for the Udio Media Manager application.

This module defines the AppConfig dataclass, which holds all configurable
settings. It provides sensible defaults and can be overridden by environment
variables for deployment flexibility.
"""

import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


def get_bool_from_env(name: str, default: bool) -> bool:
    """
    Safely retrieves a boolean value from an environment variable.
    Recognizes 'true', '1', 'yes' as True, and everything else as False.
    """
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes')


@dataclass
class AppConfig:
    """
    A dataclass holding all application configuration settings.
    This provides a single, type-safe object to pass throughout the application.
    """
    # UI Settings
    theme: str = os.getenv('UDIO_THEME', 'dark')
    window_width: int = int(os.getenv('UDIO_WINDOW_WIDTH', 1600))
    window_height: int = int(os.getenv('UDIO_WINDOW_HEIGHT', 900))
    
    # File & Path Settings
    database_path: Path = Path(os.getenv('UDIO_DB_PATH', 'udio_manager_data.db'))
    default_scan_path: Optional[Path] = os.getenv('UDIO_MEDIA_DIR')
    
    # Performance Settings
    database_timeout: float = float(os.getenv('UDIO_DB_TIMEOUT', 10.0))
    max_scan_workers: int = int(os.getenv('UDIO_SCAN_WORKERS', 4))
    
    # Feature Flags & Debugging
    debug_mode: bool = get_bool_from_env('UDIO_DEBUG', False)

    def __post_init__(self):
        """Perform type conversion for path-like objects after initialization."""
        if self.default_scan_path and isinstance(self.default_scan_path, str):
            self.default_scan_path = Path(self.default_scan_path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the configuration to a dictionary, converting Path objects to strings.
        Useful for saving configuration to a file (e.g., JSON).
        """
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """
        Creates an AppConfig instance from a dictionary.
        This safely handles converting string paths back to Path objects.
        """
        # Filter out any keys from the dictionary that are not fields in the dataclass
        config_fields = {f.name for f in cls.__dataclass_fields__}
        filtered_data = {k: v for k, v in data.items() if k in config_fields}
        
        return cls(**filtered_data)

# You can create a default instance to be imported by other modules if desired
# default_config = AppConfig()