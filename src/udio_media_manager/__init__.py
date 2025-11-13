# udio_media_manager/src/udio_media_manager/__init__.py - DEFINITIVE & CORRECTED VERSION

"""
Udio Media Manager
==================

This is the main package initialization file. Its primary purpose is to define
the application's core metadata and expose a minimal, safe public API.

To prevent circular import errors, this file intentionally avoids importing
complex modules from its own sub-packages. The application's entry points
(main.py and __main__.py) are responsible for importing and running the
Application class.
"""

# --- Package Metadata ---
__version__ = "7.1.0"
__author__ = "Your Name"
__description__ = "A comprehensive media manager for Udio tracks"

# --- Core Constants ---
# Expose only the most fundamental, top-level constants.
# These are safe to import as they have no further dependencies within the package.
from .core.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION

# --- Explicit Public API via __all__ ---
# This defines what `from udio_media_manager import *` will import.
# It is kept minimal to ensure stability. The 'main_entry' has been removed
# as the Application class is now handled by the executable scripts.
__all__ = [
    # Metadata
    '__version__',
    '__author__',
    '__description__',
    
    # Core Constants
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
]

# Optional log message to confirm the package is loaded successfully.
from .utils.logging import get_logger
logger = get_logger(__name__)
logger.debug(f"Package '{__name__}' version {__version__} loaded.")