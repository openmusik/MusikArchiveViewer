# udio_media_manager/src/udio_media_manager/ui/__init__.py - DEFINITIVE & CORRECTED VERSION

"""
User Interface Package Manifest

This file defines the public API for the entire UI package. It aggregates the most
important classes from its sub-packages (`components`, `themes`, `widgets`) into a
single, convenient namespace.

This allows other parts of the application to use clean imports like:
    from ..ui import MainWindow, ThemeManager, VirtualList, AudioController
"""

# --- Import from sub-packages using correct relative paths ---

# 1. Core Services for the UI
from .themes import ThemeManager

# 2. Reusable, Low-Level Widgets (from the .widgets sub-package)
from .widgets import (
    ClickableLabel,
    ProgressDialog,
    SearchEntry,
    StatusBar,
    ThumbnailLabel,
    ToolTip
)

# 3. High-Level, Composite Components (from the .components sub-package)
from .components import (
    MetadataView,
    TrackList,
    VirtualList,
    VirtualListItem
)

# 4. Main Application Window and Controllers
from .main_window import MainWindow
from .audio_controller import AudioController
from .event_handlers import EventHandlers
from .scan_manager import ScanManager


# --- Explicitly define the public API for the 'ui' package ---
__all__ = [
    # Core Services
    'ThemeManager',

    # Low-Level Widgets
    'ClickableLabel',
    'ProgressDialog',
    'SearchEntry',
    'StatusBar',
    'ThumbnailLabel',
    'ToolTip',

    # High-Level Components
    'MetadataView',
    'TrackList',
    'VirtualList',
    'VirtualListItem',

    # Main Window & Controllers
    'MainWindow',
    'AudioController',
    'EventHandlers',
    'ScanManager',
]