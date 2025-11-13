"""
RECYCLABLE Track List Item with PROPER TRACK UPDATES

This RECYCLABLE VERSION features:
- ✅ PROPER TRACK UPDATES - Can change track data when recycled
- ✅ COMPLETE STATE RESET - All state cleared when track changes
- ✅ WORKING EVENT HANDLERS - Click and selection work correctly
- ✅ CLEAN ARTWORK MANAGEMENT - Proper artwork cancellation on track change
"""

import tkinter as tk
from tkinter import ttk
import weakref
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from ...domain.models import Track
    from ...services import ImageLoader
    from PIL.ImageTk import PhotoImage

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
    RECYCLABLE VERSION: Can be reused for different tracks with proper state reset.
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
        image_loader: "ImageLoader",
        on_double_click: Optional[Callable[["Track"], None]] = None,
        on_select: Optional[Callable[["Track"], None]] = None
    ):
        # CRITICAL: Don't store track in constructor - it will change when recycled
        self.track: Optional["Track"] = None
        self.image_loader = image_loader
        self.on_double_click_callback = on_double_click
        self.on_select_callback = on_select
        
        # State management
        self._state = TrackItemState.NORMAL
        self._pending_artwork_id: Optional[str] = None
        self._photo_ref: Optional[Any] = None
        self._is_destroyed = False
        self._current_track_id: Optional[str] = None
        
        # Widget references
        self.widgets = TrackWidgets()

    def get_height(self) -> int:
        """Returns the fixed height of this item."""
        return self.HEIGHT

    def set_track(self, track: "Track") -> None:
        """
        CRITICAL: Set or update the track for this item.
        Called when item is recycled to show a different track.
        """
        # Cancel any pending artwork for previous track
        self._cancel_pending_artwork()
        
        # Clear photo reference for previous track
        self._photo_ref = None
        
        # Update track reference
        self.track = track
        self._current_track_id = getattr(track, 'song_id', id(track))
        
        # Reset to default state
        self._state = TrackItemState.NORMAL
        
        logger.debug(f"🔄 TrackListItem assigned to: {track.title}")

    def create_widget(self, parent: tk.Widget) -> ttk.Frame:
        """
        Creates the frame and all child widgets.
        """
        if self._is_destroyed:
            logger.warning("🚫 Attempted to create widget for destroyed item")
            return ttk.Frame(parent)
        
        # CRITICAL: Must have a track assigned before creating widget
        if not self.track:
            logger.error("❌ Cannot create widget: no track assigned")
            return ttk.Frame(parent)
        
        try:
            # Create main frame
            self.widgets.frame = ttk.Frame(
                parent, 
                height=self.HEIGHT, 
                style='TrackItem.TFrame'
            )
            self.widgets.frame.pack_propagate(False)
            
            # Store track reference for recycling validation
            self.widgets.frame._current_track_id = self._current_track_id
            self.widgets.frame._list_item_ref = weakref.ref(self)
            
            # Configure grid columns
            self._setup_grid_columns()
            
            # Create all child widgets with CURRENT track data
            self._create_child_widgets()
            
            # Set up event bindings
            self._bind_events()
            
            logger.debug(f"✅ Widget created for: {self.track.title}")
            return self.widgets.frame
            
        except Exception as e:
            logger.error(f"❌ Failed to create widget for {self.track.title if self.track else 'NO TRACK'}: {e}")
            fallback_frame = ttk.Frame(parent, height=self.HEIGHT)
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
        """Creates all child widgets with CURRENT track data."""
        if not self.widgets.frame or not self.track:
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
            text=self.track.title or "Untitled",
            anchor='w',
            style='TrackTitle.TLabel'
        )
        self._place_widget('title', self.widgets.title)

        # Artist widget
        self.widgets.artist = ttk.Label(
            self.widgets.frame,
            text=self.track.artist or "Unknown Artist",
            anchor='w',
            style='TrackArtist.TLabel'
        )
        self._place_widget('artist', self.widgets.artist)

        # Metadata widgets
        self.widgets.duration = ttk.Label(
            self.widgets.frame,
            text=getattr(self.track, 'duration_formatted', '--:--'),
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('duration', self.widgets.duration)

        self.widgets.plays = ttk.Label(
            self.widgets.frame,
            text=str(getattr(self.track, 'plays', 0)),
            anchor='center', 
            style='TrackMeta.TLabel'
        )
        self._place_widget('plays', self.widgets.plays)

        self.widgets.likes = ttk.Label(
            self.widgets.frame,
            text=str(getattr(self.track, 'likes', 0)),
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('likes', self.widgets.likes)

        self.widgets.date = ttk.Label(
            self.widgets.frame,
            text=self._format_date(),
            anchor='center',
            style='TrackMeta.TLabel'
        )
        self._place_widget('date', self.widgets.date)

        self.widgets.size = ttk.Label(
            self.widgets.frame,
            text=format_file_size(getattr(self.track, 'file_size', 0)),
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
        Updates the content and style.
        """
        # Basic safety check
        if self._is_destroyed or not widget.winfo_exists() or not self.track:
            return

        # Ensure widget references are correct
        if not self.widgets.frame or self.widgets.frame != widget:
            self.widgets.frame = widget
            widget._current_track_id = self._current_track_id
            widget._list_item_ref = weakref.ref(self)

        # Update state
        new_state = TrackItemState.SELECTED if is_selected else TrackItemState.NORMAL
        state_changed = new_state != self._state
        self._state = new_state

        try:
            # Update ALL content
            self._update_content()
            
            # Update styles if state changed
            if state_changed:
                self._update_styles()
                
            # Load artwork
            self._load_artwork()
            
        except Exception as e:
            logger.error(f"❌ Error updating widget for {self.track.title}: {e}")

    def _update_content(self):
        """Updates all widget content with current track data."""
        if not self.widgets.frame or not self.track:
            return

        # Update each widget with current track data
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
                    widget.config(text=value)
                except (tk.TclError, AttributeError):
                    pass

    def _format_date(self) -> str:
        """Safely formats the track date with fallback."""
        if not self.track:
            return "-"
            
        try:
            date_obj = getattr(self.track, 'created_date', None)
            if date_obj:
                return date_obj.strftime('%m/%d/%y')
        except (AttributeError, ValueError):
            pass
        return "-"

    def _update_styles(self):
        """Applies styles based on current state."""
        if not self.widgets.frame or not self.widgets.frame.winfo_exists():
            return

        # Define style mappings
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
        
        # Apply styles
        self._apply_style_safe(self.widgets.frame, styles['frame'])
        self._apply_style_safe(self.widgets.thumb, styles['thumb'])
        self._apply_style_safe(self.widgets.title, styles['title'])
        self._apply_style_safe(self.widgets.artist, styles['artist'])
        
        # Apply to metadata widgets
        for widget in [self.widgets.duration, self.widgets.plays, 
                      self.widgets.likes, self.widgets.date, self.widgets.size]:
            self._apply_style_safe(widget, styles['meta'])

    def _apply_style_safe(self, widget: Optional[ttk.Widget], style: str):
        """Safely applies a style to a widget."""
        if not widget or not widget.winfo_exists():
            return
            
        try:
            widget.config(style=style)
        except tk.TclError:
            pass

    def _load_artwork(self):
        """Loads artwork for the current track."""
        if not self.track:
            return
            
        # Cancel any previous artwork loading
        self._cancel_pending_artwork()
        
        # Basic checks
        if (not self.image_loader or not hasattr(self.track, 'art_path') or 
            not self.widgets.thumb or not self.widgets.thumb.winfo_exists()):
            self._set_default_artwork()
            return

        art_path = self.track.art_path
        if not art_path:
            self._set_default_artwork()
            return

        # Create weak reference for callback safety
        weak_self = weakref.ref(self)
        track_id = self._current_track_id
        
        def on_artwork_loaded(image: Optional["PhotoImage"]):
            """Callback for when artwork loading completes."""
            instance = weak_self()
            if not instance or instance._is_destroyed:
                return
                
            instance._pending_artwork_id = None
            
            # Validate widget still exists and shows the same track
            if (not instance.widgets.thumb or 
                not instance.widgets.thumb.winfo_exists() or
                not instance.widgets.frame or
                not instance.widgets.frame.winfo_exists() or
                getattr(instance.widgets.frame, '_current_track_id', None) != track_id):
                return
                
            instance._update_artwork_widget(image)

        # Request artwork loading
        try:
            self._pending_artwork_id = self.image_loader.load_image(
                path=art_path,
                size=(self.THUMB_SIZE, self.THUMB_SIZE),
                callback=on_artwork_loaded,
                weak_refs=[weak_self]
            )
        except Exception as e:
            logger.debug(f"Error loading artwork for {self.track.title}: {e}")
            self._set_default_artwork()

    def _set_default_artwork(self):
        """Sets the default artwork."""
        if self.widgets.thumb and self.widgets.thumb.winfo_exists():
            self.widgets.thumb.config(image='', text="🎵")

    def _update_artwork_widget(self, image: Optional[Any]):
        """Updates the thumbnail widget with loaded artwork."""
        if (self._is_destroyed or not self.widgets.thumb or 
            not self.widgets.thumb.winfo_exists()):
            return
            
        try:
            if image:
                self._photo_ref = image
                self.widgets.thumb.config(image=image, text='')
            else:
                self._set_default_artwork()
        except Exception:
            self._set_default_artwork()

    def _bind_events(self):
        """Binds mouse events for interaction."""
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
                widget.bind('<Button-1>', self._on_single_click, add='+')
                widget.bind('<Enter>', self._on_enter, add='+')
                widget.bind('<Leave>', self._on_leave, add='+')
                widget.bind('<Double-Button-1>', self._on_double_click, add='+')

    def _on_single_click(self, event: tk.Event):
        """Handle single click selection."""
        if (self._is_destroyed or not self.widgets.frame or 
            not self.widgets.frame.winfo_exists() or not self.track):
            return "break"
        
        if self.on_select_callback:
            try:
                self.on_select_callback(self.track)
                return "break"
            except Exception as e:
                logger.error(f"Error in selection callback: {e}")
        
        return "break"

    def _on_enter(self, event: tk.Event):
        """Handle mouse enter events."""
        if self._is_destroyed or not self.track:
            return
            
        if self._state == TrackItemState.SELECTED:
            self._state = TrackItemState.SELECTED_HOVERED
        else:
            self._state = TrackItemState.HOVERED
        self._update_styles()

    def _on_leave(self, event: tk.Event):
        """Handle mouse leave events."""
        if self._is_destroyed or not self.track:
            return
            
        if self._state == TrackItemState.SELECTED_HOVERED:
            self._state = TrackItemState.SELECTED
        else:
            self._state = TrackItemState.NORMAL
        self._update_styles()

    def _on_double_click(self, event: tk.Event):
        """Handle double-click events."""
        if self._is_destroyed or not self.track:
            return "break"
            
        if self.on_double_click_callback:
            self.on_double_click_callback(self.track)
        return "break"

    def _cancel_pending_artwork(self):
        """Cancels any pending artwork loading request."""
        if self._pending_artwork_id and self.image_loader:
            try:
                self.image_loader.cancel_request(self._pending_artwork_id)
            except Exception:
                pass
            finally:
                self._pending_artwork_id = None

    def destroy_widget(self, widget: tk.Widget) -> None:
        """
        Cleanup when widget is being recycled or destroyed.
        """
        if self._is_destroyed:
            return
            
        self._is_destroyed = True
        
        # Cancel pending artwork loading
        self._cancel_pending_artwork()
        
        # Clear photo reference
        self._photo_ref = None
        
        # Clear widget references
        self.widgets = TrackWidgets()
        
        # Clear track reference
        self.track = None
        self._current_track_id = None

    def __del__(self):
        """Destructor."""
        pass