# udio_media_manager/src/udio_media_manager/ui/components/__init__.py - FULLY UPGRADED

"""
UI Components Package Manifest
==============================

This package defines the public API for the high-level, composite UI components
of the application. A "component" is a complex element made up of several
smaller widgets (e.g., a full track list, a metadata viewer).

- For low-level, reusable widgets (like a custom button or search bar),
  import from the `udio_media_manager.ui.widgets` package.
- For high-level, application-specific components, import from here.
"""

# --- High-Level Component Imports ---

# A composite view for displaying all detailed track metadata.
from .metadata_view import MetadataView

# The main body of the track list, aliased as `TrackList` for convenient use.
from .track_list_body import TrackListBody as TrackList

# The core virtual list engine and its abstract item base class from the sub-package.
from .virtual_list import VirtualList, VirtualListItem


# --- Public API Definition ---
# This list explicitly declares which components are intended for use by other
# parts of the application (e.g., by MainWindow). It correctly contains ONLY
# high-level components.
__all__ = [
    # Composite view components
    'MetadataView',
    'TrackList',

    # Core virtual list engine, which is a foundational component
    'VirtualList',
    'VirtualListItem',
]