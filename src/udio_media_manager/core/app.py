# udio_media_manager/src/udio_media_manager/core/app.py - FULLY UPGRADED

"""
Core Application Class and Main Entry Point.

This module orchestrates the entire application lifecycle, from component
assembly to robust, deterministic shutdown.
"""

import sys
import traceback
import tempfile
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from filelock import FileLock, Timeout
from typing import Optional, TYPE_CHECKING

# Use TYPE_CHECKING for type hints to avoid circular imports at runtime
if TYPE_CHECKING:
    from ..services import UdioService, AudioPlayer, ImageLoader
    from ..ui import MainWindow, ThemeManager, AudioController, ScanManager, EventHandlers

from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def _show_transient_error_popup(title: str, message: str) -> None:
    """Creates a temporary root window to display a critical error message."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(title, message)
        root.destroy()
    except Exception:
        print(f"[{title.upper()}] {message}", file=sys.stderr)

class Application:
    """
    Encapsulates the entire application lifecycle, including robust startup,
    component assembly, and a deterministic shutdown sequence to prevent crashes.
    """
    def __init__(self, **kwargs):
        self.lock_path = Path(tempfile.gettempdir()) / "udio_media_manager.lock"
        self.lock = FileLock(self.lock_path, timeout=1)
        self.app_instance: Optional["MainWindow"] = None
        self.exit_code = 1
        self.cli_args = kwargs
        self._is_shutting_down = False

    def run(self) -> None:
        """Main entry point that manages the application lock and top-level exceptions."""
        log_level = self.cli_args.get('log_level', 'INFO').upper()
        # Use a more robust setup call that handles potential spam from libraries
        setup_logging(console_level=log_level, enable_quiet_mode=True, enable_spam_filters=True)
        
        logger.info("=" * 53)
        logger.info("Udio Media Manager - Application Starting")
        logger.info("=" * 53)
        try:
            with self.lock:
                logger.info(f"Acquired single-instance lock at: {self.lock_path}")
                self._setup_global_exception_handlers()
                self.exit_code = self._run_gui_app()
        except Timeout:
            logger.warning(f"Another instance is running. Lock file: {self.lock_path}")
            _show_transient_error_popup("Already Running", "Another instance of Udio Media Manager is already running.")
            self.exit_code = 1
        except Exception:
            logger.critical("Fatal error in main entry point.", exc_info=True)
            self.exit_code = 1
        finally:
            self._shutdown_logging()
            sys.exit(self.exit_code)

    def _on_window_close(self) -> None:
        """
        Handles the window close event ('WM_DELETE_WINDOW'). This is the
        primary entry point for a clean, deterministic shutdown.
        """
        if self._is_shutting_down: return
        self._is_shutting_down = True
        logger.info("Window close requested. Initiating shutdown sequence.")
        if self.app_instance:
            self.app_instance.shutdown()
        # Check for root existence before destroying
        if self.app_instance and self.app_instance.root and self.app_instance.root.winfo_exists():
            self.app_instance.root.destroy()

    def _run_gui_app(self) -> int:
        """Orchestrates the creation, connection, and running of the GUI application."""
        from ..services import UdioService, AudioPlayer, ImageLoader
        from ..ui import MainWindow, ThemeManager, AudioController, ScanManager, EventHandlers

        root = tk.Tk()
        try:
            # --- PHASE 1: ASSEMBLY ---
            logger.info("--- APPLICATION ASSEMBLY ---")
            udio_service = UdioService()
            audio_player = AudioPlayer()
            image_loader = ImageLoader()
            theme_manager = ThemeManager()
            
            # --- ENHANCEMENT: Inject root dependency into ImageLoader ---
            # This is crucial for ImageLoader to schedule UI updates on the main thread.
            image_loader.set_root(root)
            
            self.app_instance = MainWindow(root, udio_service, audio_player, image_loader, theme_manager)
            audio_controller = AudioController(audio_player, self.app_instance)
            scan_manager = ScanManager(udio_service, self.app_instance)
            event_handlers = EventHandlers(self.app_instance)

            # --- PHASE 2: CONNECTION (Dependency Injection) ---
            logger.info("Step 3: Connecting controllers and managers...")
            event_handlers.setup_managers(audio_controller, scan_manager)
            
            # --- PHASE 3: UI BUILD & LAYOUT ---
            logger.info("Step 4: Initializing theme and building widgets...")
            theme_manager.initialize(root)
            self.app_instance.build_all(event_handlers.get_ui_callbacks())
            
            # --- PHASE 4: BINDING AND SHUTDOWN PROTOCOL ---
            logger.info("Step 6: Binding events and setting shutdown protocol...")
            root.protocol("WM_DELETE_WINDOW", self._on_window_close)
            root.report_callback_exception = self._global_exception_handler
            event_handlers.bind_global_events()
            event_handlers.register_system_callbacks()
            root.title("Udio Media Manager")
            root.geometry("1400x800")
            
            # --- PHASE 5: RUN ---
            
            # ✅ CRITICAL FIX: Use `after_idle` to run the initial data load.
            # This waits for the UI to finish its initial drawing, making the
            # app feel more responsive and preventing the double-refresh race condition.
            root.after_idle(self.app_instance.refresh_tracks)
            
            # ❌ REMOVED: The old `root.after(500, ...)` which caused the problem.
            
            root.mainloop()
            
            return 0
        except Exception:
            logger.critical("Fatal error during application startup or runtime.", exc_info=True)
            return 1

    def _setup_global_exception_handlers(self) -> None:
        """Sets a top-level exception hook to catch any unhandled errors."""
        sys.excepthook = self._global_exception_handler
        logger.info("Global exception handlers installed.")

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback) -> None:
        """Logs critical errors and shows a popup to the user."""
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        logger.critical("Unhandled exception caught by global handler:", exc_info=(exc_type, exc_value, exc_traceback))
        error_message = f"A critical error occurred: {exc_value}\n\nCheck logs for details."
        _show_transient_error_popup("Fatal Error", error_message)

    def _shutdown_logging(self) -> None:
        """Logs the final application exit message."""
        logger.info("=" * 53)
        logger.info("Udio Media Manager - Application Shutdown")
        logger.info(f"Exiting with code {self.exit_code}")
        logger.info("=" * 53)