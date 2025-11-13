# udio_media_manager/ui/main_window.py - DEBUGGED & CORRECTED VERSION

"""
UI Component Factory and Application Window - WITH SELECTION DEBUGGING

This module defines the main application class, which is responsible for creating
and holding references to all core UI widgets, services, and controllers. It acts
as the central orchestrator for data state, filtering, and the crucial
shutdown sequence.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, TYPE_CHECKING

# Necessary imports for data manipulation
from ..domain.dto import TrackQueryDTO
from ..domain.enums import SortKey
from ..utils.logging import get_logger

# --- CRITICAL FIX IS HERE ---
# Widgets are imported from the .widgets sub-package.
# Components are imported from the .components sub-package.
from .widgets import SearchEntry, StatusBar
from .components import TrackList, MetadataView
# --- END OF CRITICAL FIX ---

if TYPE_CHECKING:
    from ..services import UdioService, AudioPlayer, ImageLoader
    from .themes import ThemeManager
    from ..domain.models import Track

logger = get_logger(__name__)

class MainWindow:
    """
    A factory and registry for all UI widgets and application state.
    Manages building the UI, handling data state (query/sort), and lifecycle.
    """
    
    def __init__(self, root: tk.Tk, service: "UdioService", audio_player: "AudioPlayer", image_loader: "ImageLoader", theme_manager: "ThemeManager"):
        self.root = root
        self.service = service
        self.audio_player = audio_player
        self.image_loader = image_loader
        self.theme = theme_manager
        
        # --- Data & State ---
        self.current_track: Optional["Track"] = None
        self._is_built = False
        self._is_shutting_down = False
        self.current_query = TrackQueryDTO(sort_by=SortKey.DATE, sort_descending=True)

        # --- Control Variables ---
        self.dir_var = tk.StringVar(value=str(Path.home() / "Music"))
        self.track_count_var = tk.StringVar(value="0 Tracks")
        self.now_playing_track_var = tk.StringVar(value="No track selected.")

        # --- Component References ---
        self.header_frame: Optional[ttk.Frame] = None
        self.main_paned_window: Optional[ttk.PanedWindow] = None
        self.audio_controls_frame: Optional[ttk.Frame] = None
        self.status_bar: Optional[StatusBar] = None
        self.track_list: Optional[TrackList] = None
        self.metadata_view: Optional[MetadataView] = None
        self.search_entry: Optional[SearchEntry] = None
        self.dir_frame: Optional[ttk.Frame] = None
        self.action_frame: Optional[ttk.Frame] = None
        self.transport_frame: Optional[ttk.Frame] = None
        
        logger.info("🎯 MainWindow initialized - SELECTION DEBUGGING ENABLED")

    def build_all(self, callbacks: Dict[str, Callable]) -> None:
        """Creates and lays out all UI sections and their child widgets."""
        if self._is_built:
            logger.warning("build_all called more than once. Ignoring.")
            return

        logger.info("🎯 Building all UI component instances with callback debugging...")
        
        # DEBUG: Log all available callbacks
        logger.debug("🎯 AVAILABLE CALLBACKS:")
        for callback_name, callback_func in callbacks.items():
            logger.debug(f"🎯   {callback_name}: {callback_func}")
        
        # CRITICAL: Check if selection callbacks exist
        on_track_select = callbacks.get('on_track_select')
        on_track_double_click = callbacks.get('on_track_double_click')
        
        if not on_track_select:
            logger.error("❌ CRITICAL: on_track_select callback is MISSING!")
        else:
            logger.info("✅ on_track_select callback found")
            
        if not on_track_double_click:
            logger.error("❌ CRITICAL: on_track_double_click callback is MISSING!")
        else:
            logger.info("✅ on_track_double_click callback found")

        try:
            self._create_components(callbacks)
            self._layout_components()
            self._is_built = True
            
            # TEST: Verify callback chain after building
            self._test_callback_chain()
            
            logger.info("✅ All UI components built and laid out successfully.")
        except Exception:
            logger.critical("❌ Critical error building UI components.", exc_info=True)
            raise

    def _create_components(self, callbacks: Dict[str, Callable]):
        """Instantiates all major UI components and widgets."""
        self.header_frame = ttk.Frame(self.root, padding="10", style='Card.TFrame')
        self.main_paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.audio_controls_frame = ttk.Frame(self.root, padding="10", style='Card.TFrame')
        self.status_bar = StatusBar(self.root)

        self.dir_frame = ttk.Frame(self.header_frame)
        ttk.Label(self.dir_frame, text="Music Directory:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(self.dir_frame, textvariable=self.dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.dir_frame, text="Browse...", command=callbacks.get('on_browse')).pack(side=tk.LEFT, padx=(5, 0))
        
        self.action_frame = ttk.Frame(self.header_frame)
        self.search_entry = SearchEntry(self.action_frame, on_search=callbacks.get('on_search'), on_clear=callbacks.get('on_search_clear'))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.action_frame, text="Scan", command=callbacks.get('on_scan'), style='Primary.TButton').pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(self.action_frame, text="Refresh", command=callbacks.get('on_refresh')).pack(side=tk.LEFT, padx=5)

        left_pane = ttk.Frame(self.main_paned_window)
        
        # CRITICAL: TrackList initialization with callback verification
        logger.debug("🎯 Initializing TrackList with callbacks...")
        self.track_list = TrackList(
            left_pane, 
            image_loader=self.image_loader, 
            on_select=callbacks.get('on_track_select'), 
            on_double_click=callbacks.get('on_track_double_click')
        )
        logger.debug(f"🎯 TrackList created: {self.track_list}")
        
        right_pane = ttk.Frame(self.main_paned_window, padding=5)
        self.metadata_view = MetadataView(right_pane)
        logger.debug(f"🎯 MetadataView created: {self.metadata_view}")

        self.main_paned_window.add(left_pane, weight=3)
        self.main_paned_window.add(right_pane, weight=2)

        self.transport_frame = ttk.Frame(self.audio_controls_frame)
        ttk.Button(self.transport_frame, text="⏮", command=callbacks.get('on_previous')).pack(side=tk.LEFT)
        ttk.Button(self.transport_frame, text="▶", command=callbacks.get('on_play_pause'), style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(self.transport_frame, text="⏹", command=callbacks.get('on_stop')).pack(side=tk.LEFT)
        ttk.Button(self.transport_frame, text="⏭", command=callbacks.get('on_next')).pack(side=tk.LEFT, padx=5)

    def _layout_components(self) -> None:
        """Places all created components onto the main window."""
        self.header_frame.pack(fill='x', padx=10, pady=(10, 5))
        self.main_paned_window.pack(fill='both', expand=True, padx=10)
        self.audio_controls_frame.pack(fill='x', padx=10, pady=5)
        self.status_bar.pack(fill='x', side='bottom')
        self.dir_frame.pack(fill=tk.X, pady=(0, 10))
        self.action_frame.pack(fill=tk.X)
        
        # CRITICAL: Make sure TrackList is properly packed
        if self.track_list:
            self.track_list.pack(fill=tk.BOTH, expand=True)
            logger.debug("✅ TrackList packed successfully")
        else:
            logger.error("❌ TrackList is None during layout!")
            
        if self.metadata_view:
            self.metadata_view.pack(fill=tk.BOTH, expand=True)
            logger.debug("✅ MetadataView packed successfully")
        else:
            logger.error("❌ MetadataView is None during layout!")
            
        self.transport_frame.pack()
        ttk.Label(self.audio_controls_frame, textvariable=self.now_playing_track_var, anchor='center').pack(fill=tk.X, pady=(5,0))

    def _test_callback_chain(self) -> None:
        """Test the complete callback chain for debugging"""
        logger.info("🧪 TESTING CALLBACK CHAIN...")
        
        # Test 1: Check if TrackList received callbacks
        if self.track_list:
            logger.info(f"🧪 TrackList.on_select: {getattr(self.track_list, 'on_select', 'MISSING')}")
            logger.info(f"🧪 TrackList.on_double_click: {getattr(self.track_list, 'on_double_click', 'MISSING')}")
        else:
            logger.error("❌ TrackList is None!")
            
        # Test 2: Check if we have tracks to test with
        if hasattr(self, 'current_track') and self.current_track:
            logger.info(f"🧪 Current track available: {self.current_track.title}")
        else:
            logger.warning("⚠️ No current track available for testing")
            
        logger.info("🧪 CALLBACK CHAIN TEST COMPLETE")

    def set_current_track(self, track: Optional["Track"]) -> None:
        """DEBUG VERSION - Set current track with extensive logging"""
        logger.debug(f"🎯 MAINWINDOW.set_current_track CALLED")
        logger.debug(f"🎯 Track received: '{track.title if track else 'None'}'")
        
        if not self._is_built: 
            logger.warning("🚫 MAINWINDOW: UI not built yet, ignoring track selection")
            return
            
        self.current_track = track
        logger.debug("✅ MAINWINDOW: Current track reference updated")
        
        # CRITICAL: Update metadata view
        if self.metadata_view:
            logger.debug("📞 MAINWINDOW: Calling metadata_view.update()")
            try:
                self.metadata_view.update(track)
                logger.debug("✅ MAINWINDOW: metadata_view.update() completed")
            except Exception as e:
                logger.error(f"❌ MAINWINDOW: Error updating metadata view: {e}", exc_info=True)
        else:
            logger.error("❌ MAINWINDOW: No metadata_view reference!")
        
        # Update now playing display
        if track:
            display_text = f"{track.title} by {track.artist}"
            self.now_playing_track_var.set(display_text)
            logger.debug(f"✅ MAINWINDOW: Now playing updated: {display_text}")
        else:
            self.now_playing_track_var.set("No track selected.")
            logger.debug("✅ MAINWINDOW: Now playing cleared")
            
        logger.debug("✅ MAINWINDOW.set_current_track COMPLETED")
    
    def update_track_list(self, tracks: List["Track"], total_count: int) -> None:
        """Update track list with debug logging"""
        logger.debug(f"🎯 MAINWINDOW.update_track_list called with {len(tracks)} tracks")
        
        if not self._is_built: 
            logger.warning("🚫 MAINWINDOW: UI not built, ignoring track list update")
            return
            
        if self.track_list:
            logger.debug("📞 MAINWINDOW: Calling track_list.set_items()")
            self.track_list.set_items(tracks, total_count)
            logger.debug("✅ MAINWINDOW: track_list.set_items() completed")
        else:
            logger.error("❌ MAINWINDOW: No track_list reference!")
            
        self.track_count_var.set(f"{total_count:,} Tracks")
        logger.debug(f"✅ MAINWINDOW: Track count updated to {total_count:,}")

    def refresh_tracks(self) -> None:
        """Refresh tracks with query debugging"""
        if not self._is_built or not self.service: 
            logger.warning("🚫 MAINWINDOW: Cannot refresh - UI not built or no service")
            return
            
        logger.info(f"🎯 Refreshing track list with query: {self.current_query}")
        try:
            tracks, total_count = self.service.get_tracks(self.current_query)
            logger.debug(f"🎯 Service returned {len(tracks)} tracks, total: {total_count}")
            self.update_track_list(tracks, total_count)
            logger.info(f"✅ Track list updated with {total_count:,} tracks.")
        except Exception as e:
            logger.error(f"❌ Error refreshing tracks: {e}", exc_info=True)

    def filter_tracks(self, search_text: str) -> None:
        """Filter tracks with search term logging"""
        logger.debug(f"🎯 MAINWINDOW.filter_tracks called with: '{search_text}'")
        self.current_query = TrackQueryDTO(
            search_text=search_text if search_text else None,
            sort_by=self.current_query.sort_by,
            sort_descending=self.current_query.sort_descending
        )
        self.refresh_tracks()

    def sort_tracks(self, sort_key: SortKey, descending: bool) -> None:
        """Sort tracks with sorting debug"""
        logger.debug(f"🎯 MAINWINDOW.sort_tracks called: {sort_key}, descending: {descending}")
        self.current_query = TrackQueryDTO(
            search_text=self.current_query.search_text,
            sort_by=sort_key,
            sort_descending=descending
        )
        self.refresh_tracks()
    
    def show_notification(self, message: str, level: str = "info") -> None:
        """Show notification with level logging"""
        logger.debug(f"🎯 MAINWINDOW.show_notification: [{level}] {message}")
        if self.status_bar: 
            self.status_bar.set_message(message, level)
    
    def shutdown(self) -> None:
        """Shutdown with proper cleanup order"""
        if self._is_shutting_down: 
            return
            
        self._is_shutting_down = True
        logger.info("🛑 Shutting down MainWindow and all child components...")
        
        # Shutdown in reverse dependency order
        if self.track_list: 
            self.track_list.shutdown()
            logger.debug("✅ TrackList shutdown")
            
        if self.image_loader: 
            self.image_loader.shutdown()
            logger.debug("✅ ImageLoader shutdown")
            
        if self.audio_player: 
            self.audio_player.shutdown()
            logger.debug("✅ AudioPlayer shutdown")
            
        logger.info("✅ MainWindow shutdown complete.")

    def force_test_selection(self, track_index: int = 0) -> None:
        """FORCE TEST: Manually trigger selection for debugging"""
        logger.info(f"🧪 FORCE TESTING SELECTION on index {track_index}")
        
        if not self.track_list:
            logger.error("❌ No track_list available for testing")
            return
            
        # Get tracks from service to test with
        tracks, _ = self.service.get_tracks(self.current_query)
        if tracks and 0 <= track_index < len(tracks):
            test_track = tracks[track_index]
            logger.info(f"🧪 Testing with track: '{test_track.title}'")
            
            # Test direct metadata update
            self.set_current_track(test_track)
            
            # Test through track list selection
            if hasattr(self.track_list, 'select_track'):
                self.track_list.select_track(test_track)
        else:
            logger.error("❌ No tracks available for testing")