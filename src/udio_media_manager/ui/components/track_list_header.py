# [file name]: track_list_header.py
"""
Track List Header Component - Handles column headers and sorting
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional

from ...domain.enums import SortKey
from ...utils.logging import get_logger
from ..themes.theme_manager import ThemeManager

logger = get_logger(__name__)


class TrackListHeader(ttk.Frame):
    """
    Handles the track list header with sortable columns
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_sort: Callable[[SortKey, bool], None],
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.theme = ThemeManager()
        self.on_sort = on_sort
        
        # Header state
        self.current_sort: SortKey = SortKey.TITLE
        self.sort_descending: bool = False
        self.header_widgets: Dict[SortKey, ttk.Label] = {}
        self.column_config: Dict[SortKey, Dict[str, Any]] = {}
        
        self._build_header_ui()
        
    def _build_header_ui(self) -> None:
        """Build the header UI with sortable columns"""
        self.configure(style='Card.TFrame', height=36)
        
        # Exact same positions as TrackListItem for alignment
        LEFT_PADDING = 12
        SELECTION_WIDTH = 20
        THUMBNAIL_SIZE = 40
        THUMBNAIL_SPACING = 8
        TOTAL_LEFT_SPACER = LEFT_PADDING + SELECTION_WIDTH + THUMBNAIL_SIZE + THUMBNAIL_SPACING

        # Column positions (must match TrackListItem exactly)
        TITLE_COL = TOTAL_LEFT_SPACER
        ARTIST_COL = TITLE_COL + 200
        DURATION_COL = ARTIST_COL + 120
        PLAYS_COL = DURATION_COL + 60
        LIKES_COL = PLAYS_COL + 50
        CREATED_COL = LIKES_COL + 50
        FILESIZE_COL = CREATED_COL + 70

        # Column widths
        TITLE_WIDTH = 190
        ARTIST_WIDTH = 110
        DURATION_WIDTH = 50
        PLAYS_WIDTH = 40
        LIKES_WIDTH = 40
        CREATED_WIDTH = 60
        FILESIZE_WIDTH = 60

        # Column configuration
        self.column_config = {
            SortKey.TITLE: {"text": "Title", "width": TITLE_WIDTH, "anchor": "w", "x_pos": TITLE_COL},
            SortKey.ARTIST: {"text": "Artist", "width": ARTIST_WIDTH, "anchor": "w", "x_pos": ARTIST_COL},
            SortKey.DURATION: {"text": "Duration", "width": DURATION_WIDTH, "anchor": "center", "x_pos": DURATION_COL},
            SortKey.PLAYS: {"text": "Plays", "width": PLAYS_WIDTH, "anchor": "center", "x_pos": PLAYS_COL},
            SortKey.LIKES: {"text": "Likes", "width": LIKES_WIDTH, "anchor": "center", "x_pos": LIKES_COL},
            SortKey.DATE: {"text": "Created", "width": CREATED_WIDTH, "anchor": "center", "x_pos": CREATED_COL},
            SortKey.FILE_SIZE: {"text": "File Size", "width": FILESIZE_WIDTH, "anchor": "center", "x_pos": FILESIZE_COL},
        }

        # Create header labels
        positions = [
            (SortKey.TITLE, "Title", TITLE_COL, TITLE_WIDTH, "w"),
            (SortKey.ARTIST, "Artist", ARTIST_COL, ARTIST_WIDTH, "w"),
            (SortKey.DURATION, "Duration", DURATION_COL, DURATION_WIDTH, "center"),
            (SortKey.PLAYS, "Plays", PLAYS_COL, PLAYS_WIDTH, "center"),
            (SortKey.LIKES, "Likes", LIKES_COL, LIKES_WIDTH, "center"),
            (SortKey.DATE, "Created", CREATED_COL, CREATED_WIDTH, "center"),
            (SortKey.FILE_SIZE, "File Size", FILESIZE_COL, FILESIZE_WIDTH, "center"),
        ]

        for sort_key, text, x_pos, width, anchor in positions:
            label = self._create_header_label(sort_key, text, x_pos, width, anchor)
            self.header_widgets[sort_key] = label

        # Add spacer for thumbnail area
        spacer_frame = ttk.Frame(self, style='Card.TFrame', width=TOTAL_LEFT_SPACER)
        spacer_frame.place(x=0, y=0, width=TOTAL_LEFT_SPACER, height=36)
        
        self._update_header_indicators()
        
    def _create_header_label(self, sort_key: SortKey, text: str, x_pos: int, width: int, anchor: str) -> ttk.Label:
        """Create a single header label with sorting behavior"""
        label_text = text
        if self.current_sort == sort_key:
            indicator = " ▾" if self.sort_descending else " ▴"
            label_text += indicator
        
        label = ttk.Label(
            self, 
            text=label_text, 
            style='Header.TLabel',
            anchor=anchor,
            cursor='hand2',
            font=('Segoe UI', 9, 'bold')
        )
        
        label.place(x=x_pos, y=6, width=width, height=24)
        label.bind('<Button-1>', lambda e, sk=sort_key: self._on_header_click(sk))
        label.bind('<Enter>', lambda e, l=label: self._on_header_hover_enter(l))
        label.bind('<Leave>', lambda e, l=label: self._on_header_hover_leave(l))
        
        return label
        
    def _on_header_click(self, sort_key: SortKey) -> None:
        """Handle header click for sorting"""
        logger.debug(f"Header clicked: {sort_key.value}")
        
        if self.current_sort == sort_key:
            self.sort_descending = not self.sort_descending
        else:
            self.current_sort = sort_key
            self.sort_descending = True

        self._update_header_indicators()
        self.on_sort(sort_key, self.sort_descending)
        
    def _on_header_hover_enter(self, label: ttk.Label) -> None:
        """Handle header hover enter"""
        if label.cget('style') != 'Active.Header.TLabel':
            label.config(style='Hover.Header.TLabel')

    def _on_header_hover_leave(self, label: ttk.Label) -> None:
        """Handle header hover leave"""
        if label.cget('style') == 'Hover.Header.TLabel':
            for sort_key, widget in self.header_widgets.items():
                if widget == label:
                    if self.current_sort == sort_key:
                        label.config(style='Active.Header.TLabel')
                    else:
                        label.config(style='Header.TLabel')
                    break

    def _update_header_indicators(self) -> None:
        """Update sort indicators on all headers"""
        for sort_key, label in self.header_widgets.items():
            if sort_key not in self.column_config:
                continue
                
            base_text = self.column_config[sort_key]["text"]
            
            if self.current_sort == sort_key:
                indicator = " ▾" if self.sort_descending else " ▴"
                label.config(text=base_text + indicator, style='Active.Header.TLabel')
            else:
                label.config(text=base_text, style='Header.TLabel')

    def set_sort(self, sort_key: SortKey, descending: bool = False) -> None:
        """Programmatically set sort order"""
        if sort_key not in self.column_config:
            logger.warning(f"Invalid sort key: {sort_key}")
            return
            
        self.current_sort = sort_key
        self.sort_descending = descending
        self._update_header_indicators()
        
    def get_current_sort(self) -> tuple[SortKey, bool]:
        """Get current sort configuration"""
        return (self.current_sort, self.sort_descending)