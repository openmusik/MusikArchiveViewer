"""
Menu construction and management - EXTRACTED from main_window.py
"""

import tkinter as tk
from typing import Any
from typing import Optional, Callable

from ..utils.logging import get_logger

logger = get_logger(__name__)

class MenuBuilder:
    """Builds and manages application menus."""
    
    def __init__(self, root: tk.Tk, main_window: Any):
        self.root = root
        self.main_window = main_window
        self.menubar: Optional[tk.Menu] = None

    def build_menu_bar(self) -> None:
        """Build the complete menu bar."""
        self.menubar = tk.Menu(self.root, tearoff=0)
        
        self._build_file_menu()
        self._build_export_menu()
        self._build_help_menu()
        
        self.root.configure(menu=self.menubar)

    def _build_file_menu(self) -> None:
        """Build File menu."""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        
        file_menu.add_command(
            label="Scan Directory…", 
            accelerator="Ctrl+S", 
            command=self._on_scan_directory
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Preferences…", 
            accelerator="Ctrl+,", 
            command=self._on_preferences
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", 
            accelerator="Ctrl+Q", 
            command=self._on_exit
        )
        
        self.menubar.add_cascade(label="File", menu=file_menu)

    def _build_export_menu(self) -> None:
        """Build Export menu."""
        export_menu = tk.Menu(self.menubar, tearoff=0)
        
        export_menu.add_command(
            label="Export CSV…", 
            command=self._on_export_csv
        )
        export_menu.add_command(
            label="Export JSON…", 
            command=self._on_export_json
        )
        
        self.menubar.add_cascade(label="Export", menu=export_menu)

    def _build_help_menu(self) -> None:
        """Build Help menu."""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        
        help_menu.add_command(
            label="Documentation", 
            command=self._on_documentation
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="About", 
            command=self._on_about
        )
        
        self.menubar.add_cascade(label="Help", menu=help_menu)

    # Menu action handlers
    def _on_scan_directory(self) -> None:
        """Handle Scan Directory menu action."""
        scan_manager = self.main_window.scan_manager
        if scan_manager:
            scan_manager.start_scan()

    def _on_preferences(self) -> None:
        """Handle Preferences menu action."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Preferences", "Preferences dialog coming soon!")

    def _on_exit(self) -> None:
        """Handle Exit menu action."""
        self.main_window.shutdown()

    def _on_export_csv(self) -> None:
        """Handle Export CSV menu action."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Export", "CSV export coming soon!")

    def _on_export_json(self) -> None:
        """Handle Export JSON menu action."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Export", "JSON export coming soon!")

    def _on_documentation(self) -> None:
        """Handle Documentation menu action."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Help", "Documentation coming soon!")

    def _on_about(self) -> None:
        """Handle About menu action."""
        import tkinter.messagebox as messagebox
        messagebox.showinfo("About", "Udio Media Manager\nComplete Metadata Edition")

    def shutdown(self) -> None:
        """Shutdown menu builder."""
        logger.debug("Menu builder shut down")