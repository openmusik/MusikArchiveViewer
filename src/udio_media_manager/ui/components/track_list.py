"""
Enhanced Track List Item with Improved Performance and Robustness

This upgraded version features:
- Better memory management with weak references
- Improved error handling and resource cleanup
- Optimized artwork loading with request deduplication
- Enhanced styling system with fallback mechanisms
- Comprehensive logging for debugging
"""

import tkinter as tk
from tkinter import ttk
import weakref
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

# Use TYPE_CHECKING to import types for static analysis only, preventing circular imports.
if TYPE_CHECKING:
    from ...domain.models import Track
    from ...services import ImageLoader

from .virtual_list.base import VirtualListItem
from ...utils.helpers import format_duration, format_file_size
from ...utils.logging import get_logger

logger = get_logger(__name__)


class TrackItemState(Enum):
    """Represents the visual state of a track list item."""
    NORMAL = "normal"
    HOVERED = "hovered"
    SELECTED = "selected"
    SELECTED_HOVERED = "selected_hovered"


@dataclass
class TrackWidgets:
    """Container for all widget references with type safety."""
    frame: Optional[ttk.Frame] = None
    thumb: Optional[ttk.Label] = None
    title: Optional[ttk.Label] = None
    artist: Optional[ttk.Label] = None
    duration: Optional[ttk.Label] = None
    plays: Optional[ttk.Label] = None
    likes: Optional[ttk.Label] = None
    date: Optional[ttk.Label] = None
    size: Optional[ttk.Label] = None


class TrackListItem(VirtualListItem):
    """
    A high-performance VirtualListItem that renders Track objects with optimized
    resource management and responsive grid layout.
    """
    
    # Constants for consistent sizing
    HEIGHT = 56
    THUMB_SIZE = 40
    COLUMN_PADDING = 5
    GRID_CONFIG = {
        'thumb': {'column': 0, 'weight': 0, 'minsize': 60, 'sticky': 'w', 'padx': (10, 0)},
        'title': {'column': 1, 'weight': 3, 'sticky': 'ew', 'padx': COLUMN_PADDING},
        'artist': {'column': 2, 'weight': 2, 'sticky': 'ew', 'padx': COLUMN_PADDING},
        'duration': {'column': 3, 'weight': 1, 'sticky': 'e', 'padx': COLUMN_PADDING},
        'plays': {'column': 4, 'weight': 1, 'sticky': 'e', 'padx': COLUMN_PADDING},
        'likes': {'column': 5, 'weight': 1, 'sticky': 'e', 'padx': COLUMN_PADDING},
        'date': {'column': 6, 'weight': 1, 'sticky': 'e', 'padx': COLUMN_PADDING},
        'size': {'column': 7, 'weight': 1, 'sticky': 'e', 'padx': (COLUMN_PADDING, 10)}
    }

    def __init__(
        self,
        track: "Track",
        image_loader: "ImageLoader",
        on_double_click: Optional[Callable[["Track"], None]] = None
    ):
        self.track = track
        self.image_loader = image_loader
        self.on_double_click_callback = on_double_click
        
        # State management
        self._state = TrackItemState.NORMAL
        self._pending_artwork_id: Optional[str] = None
        self._photo_ref: Optional[Any] = None
        self._is_destroyed = False
        
        # Widget references
        self.widgets = TrackWidgets()
        
        logger.debug(f"🆕 TrackListItem created for: {track.title}")

    def get_height(self) -> int:
        """Returns the fixed height of this item."""
        return self.HEIGHT

    def create_widget(self, parent: tk.Widget) -> ttk.Frame:
        """
        Creates the frame and all child widgets using a responsive grid layout.
        Implements comprehensive error handling.
        """
        if self._is_destroyed:
            logger.warning("🚫 Attempted to create widget for destroyed item")
            return ttk.Frame(parent)  # Return dummy frame
        
        try:
            # Create main frame
            self.widgets.frame = ttk.Frame(
                parent, 
                height=self.HEIGHT, 
                style='TrackItem.TFrame'
            )
            self.widgets.frame.pack_propagate(False)
            
            # Configure grid columns for responsive layout
            self._setup_grid_columns()
            
            # Create all child widgets
            self._create_child_widgets()
            
            # Set up event bindings
            self._bind_events()
            
            logger.debug(f"✅ Widget created for: {self.track.title}")
            return self.widgets.frame
            
        except Exception as e:
            logger.error(f"❌ Failed to create widget for {self.track.title}: {e}")
            # Return a minimal frame as fallback
            fallback_frame = ttk.Frame(parent, height=self.HEIGHT)
            ttk.Label(fallback_frame, text="Error").pack()
            return fallback_frame

    def _setup_grid_columns(self):
        """Configures the grid layout for responsive columns."""
        if not self.widgets.frame:
            return
            
        for col_config in self.GRID_CONFIG.values():
            self.widgets.frame.columnconfigure(
                col_config['column'], 
                weight=col_config.get('weight', 0),
                minsize=col_config.get('minsize', 0)
            )

    def _create_child_widgets(self):
        """Creates all child widgets and positions them in the grid."""
        if not self.widgets.frame:
            return

        # Thumbnail widget
        self.widgets.thumb = ttk.Label(
            self.widgets.frame, 
            text="🎵", 
            anchor='center',
            style='TrackThumb.TLabel'
        )
        self._place_widget('thumb', self.widgets.thumb)

        # Title widget
        self.widgets.title = ttk.Label(
            self.widgets.frame,
            anchor='w',
            style='TrackTitle.TLabel'
        )
        self._place_widget('title', self.widgets.title)

        # Artist widget  
        self.widgets.artist = ttk.Label(
            self.widgets.frame,
            anchor='w',
            style='TrackArtist.TLabel'
        )
        self._place_widget('artist', self.widgets.artist)

        # Metadata widgets
        self.widgets.duration = ttk.Label(
            self.widgets.frame,
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('duration', self.widgets.duration)

        self.widgets.plays = ttk.Label(
            self.widgets.frame,
            anchor='center', 
            style='TrackMeta.TLabel'
        )
        self._place_widget('plays', self.widgets.plays)

        self.widgets.likes = ttk.Label(
            self.widgets.frame,
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('likes', self.widgets.likes)

        self.widgets.date = ttk.Label(
            self.widgets.frame,
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('date', self.widgets.date)

        self.widgets.size = ttk.Label(
            self.widgets.frame,
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('size', self.widgets.size)

    def _place_widget(self, widget_type: str, widget: ttk.Label):
        """Places a widget in the grid according to configuration."""
        config = self.GRID_CONFIG[widget_type]
        widget.grid(
            row=0,
            column=config['column'],
            sticky=config['sticky'],
            padx=config['padx']
        )

    def update_widget(self, widget: ttk.Frame, is_selected: bool) -> None:
        """
        Updates the content and style of an existing widget.
        Optimized to only update what has changed.
        """
        if self._is_destroyed or not widget.winfo_exists():
            return

        # Update state
        new_state = TrackItemState.SELECTED if is_selected else TrackItemState.NORMAL
        state_changed = new_state != self._state
        self._state = new_state

        try:
            # Update content
            self._update_content()
            
            # Update styles if state changed
            if state_changed:
                self._update_styles()
                
            # Load artwork (async, won't block)
            self._load_artwork()
            
        except Exception as e:
            logger.error(f"❌ Error updating widget for {self.track.title}: {e}")

    def _update_content(self):
        """Updates all widget content with track data."""
        if not self.widgets.frame:
            return

        # Safely update each widget with error handling
        update_operations = [
            ('title', self.track.title or "Untitled"),
            ('artist', self.track.artist or "Unknown Artist"),
            ('duration', getattr(self.track, 'duration_formatted', '--:--')),
            ('plays', str(getattr(self.track, 'plays', 0))),
            ('likes', str(getattr(self.track, 'likes', 0))),
            ('date', self._format_date()),
            ('size', format_file_size(getattr(self.track, 'file_size', 0)))
        ]

        for widget_name, value in update_operations:
            widget = getattr(self.widgets, widget_name, None)
            if widget and widget.winfo_exists():
                try:
                    current_text = widget.cget('text')
                    if current_text != value:
                        widget.config(text=value)
                except (tk.TclError, AttributeError) as e:
                    logger.debug(f"Could not update {widget_name}: {e}")

    def _format_date(self) -> str:
        """Safely formats the track date with fallback."""
        try:
            date_obj = getattr(self.track, 'created_date', None)
            if date_obj:
                return date_obj.strftime('%m/%d/%y')
        except (AttributeError, ValueError) as e:
            logger.debug(f"Error formatting date: {e}")
        return "-"

    def _update_styles(self):
        """Applies styles based on current state with fallback mechanisms."""
        if not self.widgets.frame or not self.widgets.frame.winfo_exists():
            return

        # Define style mappings for different states
        style_map = {
            TrackItemState.NORMAL: {
                'frame': 'TrackItem.TFrame',
                'title': 'TrackTitle.TLabel', 
                'artist': 'TrackArtist.TLabel',
                'meta': 'TrackMeta.TLabel',
                'thumb': 'TrackThumb.TLabel'
            },
            TrackItemState.SELECTED: {
                'frame': 'TrackItem.Selected.TFrame',
                'title': 'TrackTitle.Selected.TLabel',
                'artist': 'TrackArtist.Selected.TLabel', 
                'meta': 'TrackMeta.Selected.TLabel',
                'thumb': 'TrackThumb.Selected.TLabel'
            },
            TrackItemState.HOVERED: {
                'frame': 'TrackItem.Hover.TFrame',
                'title': 'TrackTitle.Hover.TLabel',
                'artist': 'TrackArtist.Hover.TLabel',
                'meta': 'TrackMeta.Hover.TLabel',
                'thumb': 'TrackThumb.Hover.TLabel'
            },
            TrackItemState.SELECTED_HOVERED: {
                'frame': 'TrackItem.SelectedHover.TFrame',
                'title': 'TrackTitle.SelectedHover.TLabel',
                'artist': 'TrackArtist.SelectedHover.TLabel',
                'meta': 'TrackMeta.SelectedHover.TLabel',
                'thumb': 'TrackThumb.SelectedHover.TLabel'
            }
        }

        styles = style_map.get(self._state, style_map[TrackItemState.NORMAL])
        
        # Apply styles with safe fallbacks
        self._apply_style_safe(self.widgets.frame, styles['frame'], 'TFrame')
        self._apply_style_safe(self.widgets.thumb, styles['thumb'], 'TLabel')
        self._apply_style_safe(self.widgets.title, styles['title'], 'TLabel')
        self._apply_style_safe(self.widgets.artist, styles['artist'], 'TLabel')
        
        # Apply to metadata widgets
        for widget in [self.widgets.duration, self.widgets.plays, 
                      self.widgets.likes, self.widgets.date, self.widgets.size]:
            self._apply_style_safe(widget, styles['meta'], 'TLabel')

    def _apply_style_safe(self, widget: Optional[ttk.Widget], style: str, fallback_style: str):
        """Safely applies a style to a widget with fallback."""
        if not widget or not widget.winfo_exists():
            return
            
        try:
            widget.config(style=style)
        except tk.TclError:
            try:
                widget.config(style=fallback_style)
            except tk.TclError:
                pass  # Use default style

    def _load_artwork(self):
        """Loads artwork asynchronously with request deduplication and caching."""
        self._cancel_pending_artwork()
        
        if not self.image_loader or not hasattr(self.track, 'art_path'):
            self._set_default_artwork()
            return

        art_path = self.track.art_path
        if not art_path:
            self._set_default_artwork()
            return

        # Create weak reference for callback safety
        weak_self = weakref.ref(self)
        
        def on_artwork_loaded(image: Optional[Any], request_id: str):
            """Callback for when artwork loading completes."""
            if self._is_destroyed:
                return
                
            instance = weak_self()
            if not instance or instance._pending_artwork_id != request_id:
                return  # Stale callback
                
            instance._pending_artwork_id = None
            instance._update_artwork_widget(image)

        # Request artwork loading
        self._pending_artwork_id = self.image_loader.load_image(
            path=art_path,
            size=(self.THUMB_SIZE, self.THUMB_SIZE),
            callback=on_artwork_loaded,
            weak_refs=[weak_self]
        )

    def _set_default_artwork(self):
        """Sets the default artwork (music note icon)."""
        if self.widgets.thumb and self.widgets.thumb.winfo_exists():
            self.widgets.thumb.config(image='', text="🎵")

    def _update_artwork_widget(self, image: Optional[Any]):
        """Safely updates the thumbnail widget with loaded artwork."""
        if (self._is_destroyed or not self.widgets.thumb or 
            not self.widgets.thumb.winfo_exists()):
            return
            
        try:
            if image:
                self._photo_ref = image  # Keep reference to prevent garbage collection
                self.widgets.thumb.config(image=image, text='')
            else:
                self._set_default_artwork()
        except Exception as e:
            logger.debug(f"Error updating artwork widget: {e}")
            self._set_default_artwork()

    def _bind_events(self):
        """Binds mouse events to all widgets for consistent interaction."""
        if not self.widgets.frame:
            return
            
        # Bind to frame and all child widgets
        widgets_to_bind = [self.widgets.frame] + [
            getattr(self.widgets, attr) 
            for attr in TrackWidgets.__dataclass_fields__.keys() 
            if attr != 'frame' and getattr(self.widgets, attr) is not None
        ]

        for widget in widgets_to_bind:
            if widget and hasattr(widget, 'bind'):
                widget.bind('<Enter>', self._on_enter, add='+')
                widget.bind('<Leave>', self._on_leave, add='+')
                widget.bind('<Double-Button-1>', self._on_double_click, add='+')

    def _on_enter(self, event: tk.Event):
        """Handles mouse enter events."""
        if self._state == TrackItemState.SELECTED:
            self._state = TrackItemState.SELECTED_HOVERED
        else:
            self._state = TrackItemState.HOVERED
        self._update_styles()

    def _on_leave(self, event: tk.Event):
        """Handles mouse leave events."""
        if self._state == TrackItemState.SELECTED_HOVERED:
            self._state = TrackItemState.SELECTED
        else:
            self._state = TrackItemState.NORMAL
        self._update_styles()

    def _on_double_click(self, event: tk.Event):
        """Handles double-click events."""
        if self.on_double_click_callback:
            logger.debug(f"🎵 Double-clicked track: {self.track.title}")
            self.on_double_click_callback(self.track)
        return "break"  # Prevent event propagation

    def _cancel_pending_artwork(self):
        """Cancels any pending artwork loading request."""
        if self._pending_artwork_id and self.image_loader:
            try:
                self.image_loader.cancel_request(self._pending_artwork_id)
            except Exception as e:
                logger.debug(f"Error canceling artwork request: {e}")
            finally:
                self._pending_artwork_id = None

    def destroy_widget(self, widget: tk.Widget) -> None:
        """
        Comprehensive cleanup when widget is being recycled or destroyed.
        Prevents memory leaks and resource contention.
        """
        if self._is_destroyed:
            return
            
        self._is_destroyed = True
        logger.debug(f"🧹 Cleaning up TrackListItem: {self.track.title}")
        
        # Cancel pending artwork loading
        self._cancel_pending_artwork()
        
        # Clear photo reference
        self._photo_ref = None
        
        # Clear all widget references
        self.widgets = TrackWidgets()
        
        # Clear callbacks
        self.on_double_click_callback = None

    def __del__(self):
        """Destructor for additional safety cleanup."""
        if not self._is_destroyed:
            self.destroy_widget(None)