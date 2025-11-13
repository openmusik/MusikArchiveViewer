"""
UI Widgets Package
==================

This package exposes reusable, low-level custom Tkinter widgets, making them
available for other parts of the UI to use.

This __init__.py file uses direct, explicit imports and an `__all__` list to define
its public API. This is a robust and easy-to-debug pattern that prevents the
circular dependency issues caused by dynamic "lazy loading" approaches.
"""

# --- Direct, Explicit Imports ---
# Import all public widget classes directly from their respective modules.
# This makes dependencies clear and allows static analysis tools to work correctly.
from .custom_widgets import (
    ToolTip,
    ClickableLabel,
    SearchEntry,
    StatusBar,
    ThumbnailLabel,
    ProgressDialog
    # VirtualList and VirtualListItem are components, not widgets,
    # and should not be exposed here. They are correctly handled in
    # the ui/components/__init__.py file.
)

# --- Public API Definition ---
# This list explicitly declares which names should be accessible when
# another module, like ui_components, imports from this 'widgets' package.
__all__ = [
    'ToolTip',
    'ClickableLabel',
    'SearchEntry',
    'StatusBar',
    'ThumbnailLabel',
    'ProgressDialog',
]