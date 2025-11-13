# udio_media_manager/ui/scan_manager.py - FULLY UPGRADED

"""
Professional-Grade Directory Scanning Management
----------------------------------------------

This module provides a decoupled controller for managing the application's
directory scanning operations. It uses a state machine to robustly handle the
scan lifecycle (start, progress, cancellation, completion, error) and communicates
state changes back to the application via a decoupled callback system.
"""

from pathlib import Path
from typing import Optional, Callable, Any, TYPE_CHECKING, Dict, List
import weakref
from enum import Enum, auto
from collections import defaultdict

# Use TYPE_CHECKING to import types for static analysis, breaking circular imports.
if TYPE_CHECKING:
    from .main_window import MainWindow  # Corrected: No longer uses UIComponents
    from ..services import UdioService
    from ..domain.dto import ScanProgressDTO
    from ..domain.models import ScanResult

from ..domain.dto import ScanRequestDTO
from ..domain.enums import ScanStatus # This import was missing from the original file
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ScanState(Enum):
    """Represents the lifecycle state of the ScanManager."""
    IDLE = auto()
    SCANNING = auto()
    CANCELLING = auto()
    ERROR = auto()


class ScanManager:
    """Manages directory scanning operations and reports state via callbacks."""
    
    def __init__(self, udio_service: "UdioService", main_window: "MainWindow"):
        self.service = udio_service
        self.main_window_ref = weakref.ref(main_window)
        
        self._state: ScanState = ScanState.IDLE
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    @property
    def main_window(self) -> Optional["MainWindow"]:
        """Safely resolves the weak reference to the main window."""
        return self.main_window_ref()

    # REMOVED: setup_managers is no longer needed.

    def register_callback(self, event_type: str, callback: Callable):
        """Allows other components to listen for scan events."""
        self._callbacks.setdefault(event_type, []).append(callback)

    def _trigger_callbacks(self, event_type: str, *args, **kwargs):
        """Triggers all registered callbacks for a given scan event on the main UI thread."""
        if not (main_win := self.main_window) or not main_win.root:
            return
        
        for callback in self._callbacks.get(event_type, []):
            try:
                # Use root.after to ensure UI updates happen safely on the main thread.
                main_win.root.after(0, lambda c=callback, a=args, kw=kwargs: c(*a, **kw))
            except Exception as e:
                logger.error(f"Error scheduling callback for {event_type}: {e}", exc_info=True)

    def _set_state(self, new_state: ScanState):
        """Atomically sets the manager's state and notifies listeners."""
        if self._state == new_state:
            return
        
        logger.info(f"ScanManager state changing from {self._state.name} to {new_state.name}")
        self._state = new_state
        self._trigger_callbacks('scan_state_changed', new_state)

    def start_scan(self, directory: str, force_rescan: bool = False) -> None:
        """Starts the directory scanning process if the manager is idle."""
        if self._state is not ScanState.IDLE:
            logger.warning(f"Scan requested but manager is not idle (state: {self._state.name}). Ignoring.")
            return
            
        try:
            dir_path = Path(directory)
            if not dir_path.is_dir():
                self._handle_scan_error(f"Invalid directory provided for scan: {directory}")
                return
        except Exception as e:
            self._handle_scan_error(f"Invalid directory path: {e}")
            return
            
        logger.info(f"Starting scan of directory: {dir_path}")
        self._set_state(ScanState.SCANNING)
        scan_request = ScanRequestDTO(scan_path=dir_path, force_rescan=force_rescan)
        
        # Delegate the heavy lifting to the service layer.
        self.service.scan_directory(
            request=scan_request, 
            progress_callback=self._on_scan_progress, 
            completion_callback=self._on_scan_complete
        )

    def cancel_scan(self) -> None:
        """Requests cancellation of the ongoing scan operation."""
        if self._state is not ScanState.SCANNING:
            logger.warning(f"Cannot cancel scan; not in SCANNING state (current state: {self._state.name}).")
            return

        logger.info("Scan cancellation requested.")
        self._set_state(ScanState.CANCELLING)
        self.service.cancel_scan()

    def _on_scan_progress(self, progress: "ScanProgressDTO") -> None:
        """Handles scan progress updates from the service thread."""
        if self._state in [ScanState.SCANNING, ScanState.CANCELLING]:
            self._trigger_callbacks('scan_progress', progress)

    def _on_scan_complete(self, result: "ScanResult") -> None:
        """Handles scan completion from the service thread."""
        logger.info(f"Scan completed with status from service: {result.status.name}")
        
        # Use the ScanStatus enum for comparison
        if result.status == ScanStatus.ERROR:
            self._set_state(ScanState.ERROR)
        else:
            # Both COMPLETED and CANCELLED states in the service result
            # should return the manager to an IDLE state.
            self._set_state(ScanState.IDLE)
        
        self._trigger_callbacks('scan_complete', result)

    def _handle_scan_error(self, error_message: str) -> None:
        """Handles an unexpected error during scan setup."""
        logger.error(f"Scan setup error: {error_message}")
        self._set_state(ScanState.ERROR)
        self._trigger_callbacks('scan_error', error_message)

    def shutdown(self) -> None:
        """Shuts down the scan manager, cancelling any ongoing scan."""
        logger.info("Shutting down ScanManager...")
        if self._state is ScanState.SCANNING:
            self.cancel_scan()
        logger.info("ScanManager shutdown complete.")