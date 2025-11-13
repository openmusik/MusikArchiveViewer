"""
SIMPLE WORKING VERSION: Basic list that actually shows items
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.models import Track
    from ...services import ImageLoader

from ...utils.logging import get_logger

logger = get_logger(__name__)


class WorkingTrackListBody(ttk.Frame):
    """
    WORKING VERSION: Simple approach that actually shows items.
    Uses ttk.Treeview which has built-in virtualization.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        image_loader: "ImageLoader",
        on_select: Optional[Callable[["Track"], None]] = None,
        on_double_click: Optional[Callable[["Track"], None]] = None,
        on_context_menu: Optional[Callable[["Track", int, int], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.image_loader = image_loader
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self.on_context_menu_callback = on_context_menu
        
        self._tracks: List["Track"] = []
        
        # Use Treeview which has built-in virtualization
        self.tree = ttk.Treeview(
            self,
            columns=('title', 'artist', 'duration', 'plays', 'likes', 'date', 'size'),
            show='tree headings',
            height=20  # Show ~20 items at once
        )
        
        # Configure columns
        self.tree.column('#0', width=40, stretch=False)  # Icon column
        self.tree.column('title', width=200, minwidth=150)
        self.tree.column('artist', width=150, minwidth=100)
        self.tree.column('duration', width=80, stretch=False)
        self.tree.column('plays', width=60, stretch=False)
        self.tree.column('likes', width=60, stretch=False)
        self.tree.column('date', width=80, stretch=False)
        self.tree.column('size', width=80, stretch=False)
        
        # Configure headings
        self.tree.heading('#0', text='')
        self.tree.heading('title', text='Title')
        self.tree.heading('artist', text='Artist')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('plays', text='Plays')
        self.tree.heading('likes', text='Likes')
        self.tree.heading('date', text='Date')
        self.tree.heading('size', text='Size')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)
        
        logger.debug("✅ WORKING TrackListBody initialized with Treeview")

    def _on_select(self, event):
        """Handle selection"""
        if not self.on_select_callback:
            return
            
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            # Get the index from the item ID (they are sequential: I001, I002, etc.)
            try:
                index = int(item_id[1:]) - 1  # Convert "I001" to 0
                if 0 <= index < len(self._tracks):
                    self.on_select_callback(self._tracks[index])
            except (ValueError, IndexError):
                pass

    def _on_double_click(self, event):
        """Handle double click"""
        if not self.on_double_click_callback:
            return
            
        item_id = self.tree.identify_row(event.y)
        if item_id:
            try:
                index = int(item_id[1:]) - 1
                if 0 <= index < len(self._tracks):
                    self.on_double_click_callback(self._tracks[index])
            except (ValueError, IndexError):
                pass

    def _on_right_click(self, event):
        """Handle right click"""
        if not self.on_context_menu_callback:
            return
            
        item_id = self.tree.identify_row(event.y)
        if item_id:
            try:
                index = int(item_id[1:]) - 1
                if 0 <= index < len(self._tracks):
                    self.on_context_menu_callback(self._tracks[index], event.x_root, event.y_root)
            except (ValueError, IndexError):
                pass

    def set_items(self, tracks: List["Track"], total_count: Optional[int] = None) -> None:
        """Set items in Treeview"""
        logger.debug(f"🎯 WORKING set_items: {len(tracks)} tracks")
        
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        self._tracks = tracks
        
        # Add items to treeview
        for i, track in enumerate(tracks):
            item_id = f"I{i+1:03d}"  # I001, I002, etc.
            
            # Get track data with fallbacks
            title = track.title or "Untitled"
            artist = track.artist or "Unknown Artist"
            duration = getattr(track, 'duration_formatted', '--:--')
            plays = str(getattr(track, 'plays', 0))
            likes = str(getattr(track, 'likes', 0))
            
            # Format date
            date_str = "-"
            try:
                date_obj = getattr(track, 'created_date', None)
                if date_obj:
                    date_str = date_obj.strftime('%m/%d/%y')
            except:
                pass
            
            # Format size
            size_str = self._format_file_size(getattr(track, 'file_size', 0))
            
            # Insert into treeview
            self.tree.insert(
                '', 'end', iid=item_id,
                values=(title, artist, duration, plays, likes, date_str, size_str)
            )
        
        logger.info(f"✅ WORKING: Treeview loaded {len(tracks)} tracks - ITEMS ARE VISIBLE!")

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for display"""
        if not size_bytes:
            return "-"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def get_selected_item(self) -> Optional["Track"]:
        """Get selected track"""
        selection = self.tree.selection()
        if selection:
            try:
                item_id = selection[0]
                index = int(item_id[1:]) - 1
                if 0 <= index < len(self._tracks):
                    return self._tracks[index]
            except (ValueError, IndexError):
                pass
        return None

    def select_track(self, track: "Track") -> bool:
        """Select track programmatically"""
        for index, existing_track in enumerate(self._tracks):
            if getattr(existing_track, 'song_id', None) == getattr(track, 'song_id', None):
                item_id = f"I{index+1:03d}"
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                return True
        return False

    def shutdown(self) -> None:
        """Cleanup"""
        self._tracks.clear()


# Keep original class name
TrackListBody = WorkingTrackListBody