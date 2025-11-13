"""
Professional Window Builder for Udio Media Manager
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..core.constants import APP_NAME, DEFAULT_WINDOW_SIZE
from ..utils.logging import get_logger
from .themes import ThemeManager

logger = get_logger(__name__)

class WindowBuilder:
    """Professional window builder with theme integration"""
    
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.theme: Optional[ThemeManager] = None
        logger.debug("WindowBuilder initialized")
        
    def create_root_window(self) -> tk.Tk:
        """Create and configure the main application window"""
        try:
            logger.info("Creating professional root window")
            
            # Create root window
            self.root = tk.Tk()
            self.root.title(APP_NAME)
            
            # Set window size
            width, height = DEFAULT_WINDOW_SIZE
            self.root.geometry(f"{width}x{height}")
            
            # Set minimum size
            self.root.minsize(1000, 700)
            
            # Initialize theme manager
            self._initialize_theme()
            
            # Configure window properties
            self._configure_window_properties()
            
            logger.info("✅ Professional root window created successfully")
            return self.root
            
        except Exception as e:
            logger.error(f"❌ Failed to create root window: {e}")
            raise
    
    def _initialize_theme(self) -> None:
        """Initialize theme manager"""
        try:
            self.theme = ThemeManager()
            if hasattr(self.theme, 'initialize'):
                self.theme.initialize(self.root)
            logger.debug("Theme manager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize theme manager: {e}")
            self.theme = None
    
    def _configure_window_properties(self) -> None:
        """Configure window properties"""
        try:
            # Set window icon if available
            self._set_window_icon()
            
            # Configure window behavior
            self.root.resizable(True, True)
            
            # Set window position (center by default)
            self._center_window()
            
        except Exception as e:
            logger.warning(f"Could not configure some window properties: {e}")
    
    def _set_window_icon(self) -> None:
        """Set window icon if available"""
        try:
            from pathlib import Path
            
            # Try different icon paths
            icon_paths = [
                Path("assets/icon.ico"),
                Path("assets/icon.png"),
                Path("../assets/icon.ico"),
                Path("../../assets/icon.png"),
                Path("../../../assets/icon.ico")
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
                    logger.debug(f"Window icon set: {icon_path}")
                    return
                    
            logger.debug("No window icon found, using default")
            
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")
    
    def _center_window(self) -> None:
        """Center the window on screen"""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f'{width}x{height}+{x}+{y}')
        except Exception as e:
            logger.debug(f"Could not center window: {e}")