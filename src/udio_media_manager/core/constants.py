"""
FULLY UPGRADED Application-wide constants and configuration.
COMPLETE font definitions, theme colors, and platform-specific configurations.
"""

import platform
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

# ==============================================================================
# APPLICATION METADATA
# ==============================================================================
APP_NAME = "Udio Media Manager"
APP_VERSION = "7.1.0"
APP_DESCRIPTION = "A comprehensive, modular, high-performance media manager for Udio tracks"

# ==============================================================================
# FONT DEFINITIONS - COMPLETE SET
# ==============================================================================
FONTS: Dict[str, Tuple[str, int, str]] = {
    # Core fonts
    'main': ('Segoe UI', 10, 'normal'),
    'bold': ('Segoe UI', 10, 'bold'),
    'italic': ('Segoe UI', 10, 'italic'),
    
    # Header fonts
    'header': ('Segoe UI', 12, 'bold'),
    'subheader': ('Segoe UI', 11, 'bold'),
    'title': ('Segoe UI', 14, 'bold'),
    
    # Component-specific fonts
    'button': ('Segoe UI', 10, 'normal'),
    'label': ('Segoe UI', 10, 'normal'),
    'input': ('Segoe UI', 10, 'normal'),
    
    # Special fonts
    'monospace': ('Consolas', 10, 'normal'),
    'small': ('Segoe UI', 9, 'normal'),
    'large': ('Segoe UI', 12, 'normal'),
    
    # Legacy compatibility (your existing fonts)
    'head': ('Segoe UI Semibold', 13, 'normal'),
    'mono': ('Consolas', 9, 'normal'),
}

# Platform-specific font adjustments
if platform.system() == "Darwin":  # macOS
    FONTS.update({
        'main': ('SF Pro Text', 12, 'normal'),
        'bold': ('SF Pro Text Semibold', 12, 'bold'),
        'header': ('SF Pro Display Semibold', 14, 'bold'),
        'subheader': ('SF Pro Display', 13, 'bold'),
        'title': ('SF Pro Display', 16, 'bold'),
        'monospace': ('SF Mono', 11, 'normal'),
        'small': ('SF Pro Text', 10, 'normal'),
        'large': ('SF Pro Text', 14, 'normal'),
        'head': ('SF Pro Display Semibold', 14, 'normal'),
        'mono': ('SF Mono', 11, 'normal'),
    })
elif platform.system() == "Linux":
    FONTS.update({
        'main': ('Ubuntu', 10, 'normal'),
        'bold': ('Ubuntu Medium', 10, 'bold'),
        'header': ('Ubuntu Medium', 13, 'bold'),
        'subheader': ('Ubuntu', 12, 'bold'),
        'title': ('Ubuntu', 15, 'bold'),
        'monospace': ('DejaVu Sans Mono', 9, 'normal'),
        'small': ('Ubuntu', 8, 'normal'),
        'large': ('Ubuntu', 12, 'normal'),
        'head': ('Ubuntu Medium', 13, 'normal'),
        'mono': ('DejaVu Sans Mono', 9, 'normal'),
    })

# ==============================================================================
# THEME COLORS - COMPLETE SET
# ==============================================================================
THEME_COLORS: Dict[str, Dict[str, str]] = {
    "light": {
        # Core colors
        "bg": "#FAFAFA",
        "card_bg": "#FFFFFF",
        "card": "#F5F5F5", 
        "hover": "#E5F1FB",
        "selected": "#D4E6F7",
        "accent": "#0078D4",
        "accent_hover": "#106EBE",
        
        # Text colors
        "text": "#1A1A1A",
        "text_muted": "#666666",
        "text_accent": "#0078D4",
        
        # Status colors
        "success": "#28a745",
        "warning": "#ffc107", 
        "error": "#dc3545",
        "info": "#17a2b8",
        
        # Border and divider
        "border": "#E0E0E0",
        "divider": "#F0F0F0",
        
        # Interactive states
        "disabled": "#CCCCCC",
        "focus": "#0078D4",
        
        # Specific component colors
        "header_bg": "#FFFFFF",
        "sidebar_bg": "#F8F9FA",
        "status_bg": "#FFFFFF",
        
        # Scrollbar
        "scrollbar_bg": "#C0C0C0",
        "scrollbar_trough": "#F0F0F0",
        
        # Input fields
        "input_bg": "#FFFFFF",
        "input_border": "#E0E0E0",
        "input_focus": "#0078D4",
        
        # Legacy compatibility
        "muted": "#666666",
    },
    "dark": {
        # Core colors
        "bg": "#1E1E1E",
        "card_bg": "#2D2D2D",
        "card": "#2D2D2D",
        "hover": "#3A3A3A",
        "selected": "#2A4D6E",
        "accent": "#0A84FF",
        "accent_hover": "#0070E0",
        
        # Text colors
        "text": "#E0E0E0", 
        "text_muted": "#9E9E9E",
        "text_accent": "#0A84FF",
        
        # Status colors
        "success": "#34C759",
        "warning": "#FFD60A",
        "error": "#FF453A",
        "info": "#5AC8FA",
        
        # Border and divider
        "border": "#404040",
        "divider": "#333333",
        
        # Interactive states
        "disabled": "#555555",
        "focus": "#0A84FF",
        
        # Specific component colors
        "header_bg": "#252525",
        "sidebar_bg": "#252525",
        "status_bg": "#2A2A2A",
        
        # Scrollbar
        "scrollbar_bg": "#404040",
        "scrollbar_trough": "#2D2D2D",
        
        # Input fields
        "input_bg": "#2D2D2D",
        "input_border": "#404040",
        "input_focus": "#0A84FF",
        
        # Legacy compatibility
        "muted": "#9E9E9E",
    }
}

# ==============================================================================
# UI CONSTANTS
# ==============================================================================
DEFAULT_WINDOW_SIZE: Tuple[int, int] = (1600, 900)
MIN_WINDOW_SIZE: Tuple[int, int] = (1200, 700)
LIST_ITEM_HEIGHT: int = 60
THUMBNAIL_SIZE: Tuple[int, int] = (48, 48)
IMAGE_CACHE_SIZE: int = 1000

# ==============================================================================
# FILE SYSTEM CONSTANTS
# ==============================================================================
SUPPORTED_EXTENSIONS: List[str] = [
    ".mp3", ".mp4", ".avif", ".txt", ".lrc", 
    ".wav", ".flac", ".png", ".jpg", ".jpeg", ".webp"
]

MAX_FILE_SIZE_MB: int = 50  # Maximum file size to process (in MB)

# Pattern matching
UUID_PATTERN: re.Pattern = re.compile(
    r"\[([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})\](?=\.\w+$)"
)

# File type categories
AUDIO_FORMATS: List[str] = [".mp3", ".wav", ".flac", ".mp4", ".m4a", ".ogg"]
IMAGE_FORMATS: List[str] = [".avif", ".png", ".jpg", ".jpeg", ".webp"]
METADATA_FORMATS: List[str] = [".txt", ".lrc", ".json"]

# ==============================================================================
# DATABASE CONSTANTS
# ==============================================================================
DATABASE_NAME: str = "udio_tracks_v2.db"
DATABASE_TIMEOUT: float = 30.0
BATCH_INSERT_SIZE: int = 100

# ==============================================================================
# PERFORMANCE CONSTANTS
# ==============================================================================
MAX_WORKER_THREADS: int = 4
SCAN_BATCH_SIZE: int = 50
IMAGE_LOAD_TIMEOUT: int = 10  # seconds
MAX_MEMORY_CACHE_SIZE: int = 1000

# ==============================================================================
# DEFAULT SCAN DIRECTORIES
# ==============================================================================
DEFAULT_SCAN_DIRECTORIES: Dict[str, List[Path]] = {
    "Windows": [
        Path.home() / "Downloads",
        Path.home() / "Music", 
        Path.home() / "Documents" / "Udio",
        Path.home() / "OneDrive" / "Music",
        Path.home() / "Music" / "Udio",
    ],
    "Darwin": [  # macOS
        Path.home() / "Downloads",
        Path.home() / "Music",
        Path.home() / "Documents" / "Udio",
        Path.home() / "Music" / "Udio",
    ],
    "Linux": [
        Path.home() / "Downloads",
        Path.home() / "Music",
        Path.home() / "Udio",
        Path.home() / "music" / "udio",
    ]
}

def get_default_scan_directories() -> List[Path]:
    """Get platform-appropriate default scan directories."""
    system = platform.system()
    directories = DEFAULT_SCAN_DIRECTORIES.get(system, DEFAULT_SCAN_DIRECTORIES["Windows"])
    
    # Only return directories that actually exist
    return [d for d in directories if d.exists() and d.is_dir()]

# ==============================================================================
# AUDIO PLAYBACK CONSTANTS
# ==============================================================================
DEFAULT_VOLUME: int = 75
MAX_VOLUME: int = 100
AUDIO_BUFFER_SIZE: int = 4096

# ==============================================================================
# VALIDATION CONSTANTS
# ==============================================================================
MAX_TITLE_LENGTH: int = 200
MAX_ARTIST_LENGTH: int = 100
MAX_TAGS_COUNT: int = 20
MAX_FILENAME_LENGTH: int = 255
MIN_DURATION: float = 0.1  # seconds
MAX_DURATION: float = 3600.0  # 1 hour

# ==============================================================================
# EXPORT CONSTANTS
# ==============================================================================
EXPORT_FORMATS: List[str] = ['json', 'csv', 'xml']
MAX_EXPORT_ROWS: int = 10000
EXPORT_CHUNK_SIZE: int = 1000

# ==============================================================================
# SEARCH AND FILTER CONSTANTS
# ==============================================================================
MAX_SEARCH_RESULTS: int = 1000
SEARCH_DEBOUNCE_MS: int = 300  # milliseconds
MIN_SEARCH_QUERY_LENGTH: int = 2

# ==============================================================================
# ERROR AND LOGGING CONSTANTS
# ==============================================================================
MAX_LOG_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT: int = 5
MAX_ERROR_MESSAGE_LENGTH: int = 1000

# ==============================================================================
# COMPATIBILITY CONSTANTS
# ==============================================================================
# Legacy support for existing code
def get_font(name: str) -> Tuple[str, int, str]:
    """Get font tuple with fallback support."""
    return FONTS.get(name, FONTS['main'])

def get_color(theme: str, color_name: str) -> str:
    """Get color with fallback support."""
    theme_colors = THEME_COLORS.get(theme, THEME_COLORS['dark'])
    return theme_colors.get(color_name, theme_colors.get('text', '#FFFFFF'))


# Supported file extensions
SUPPORTED_EXTENSIONS = {
    # Audio
    '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma',
    # Video  
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv',
    # Metadata
    '.txt', '.json', '.xml', '.md',
    # Lyrics
    '.lrc', '.srt',
    # Images (including AVIF)
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif', '.tiff', '.svg'
}