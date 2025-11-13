"""
Scroll and navigation management
"""

import tkinter as tk
import time  # ADD THIS IMPORT
from typing import Optional, Callable

# Fix import path
from udio_media_manager.utils.logging import get_logger

logger = get_logger(__name__)

class ScrollManager:
    """
    Manages scrolling, navigation, and infinite scroll detection.
    """
    
    def __init__(self, virtual_list, item_height: int, load_threshold: int, buffer_items: int):
        self.virtual_list = virtual_list
        self.item_height = item_height
        self.load_threshold = load_threshold
        self.buffer_items = buffer_items
        
        # State
        self._last_scroll_pos: float = 0.0
        self._last_scroll_direction: str = "down"
        self._was_at_bottom_before_load: bool = False
        self._last_load_time: float = 0.0
        self._load_cooldown: float = 0.5
        
        # UI components
        self.canvas: Optional[tk.Canvas] = None
        self.scrollbar: Optional[tk.Scrollbar] = None
        
        # Callbacks
        self.on_scroll: Optional[Callable[[], None]] = None
        self.on_load_more: Optional[Callable[[], None]] = None

    def set_canvas(self, canvas: tk.Canvas, scrollbar: tk.Scrollbar) -> None:
        """Set canvas and scrollbar references."""
        self.canvas = canvas
        self.scrollbar = scrollbar

    def on_scrollbar_scroll(self, *args) -> None:
        """Handle scrollbar movement."""
        if self.canvas:
            self.canvas.yview(*args)
        self._check_infinite_scroll()
        if self.on_scroll:
            self.on_scroll()

    def on_canvas_scroll(self, first: str, last: str) -> None:
        """Handle canvas scroll updates."""
        if self.scrollbar:
            self.scrollbar.set(first, last)
        
        try:
            current_pos = float(first)
        except (ValueError, TypeError):
            current_pos = 0.0
            
        # Track scroll direction
        if current_pos > self._last_scroll_pos:
            self._last_scroll_direction = "down"
        elif current_pos < self._last_scroll_pos:
            self._last_scroll_direction = "up"
        self._last_scroll_pos = current_pos
        
        self._was_at_bottom_before_load = self.is_at_bottom(threshold=2)
        self._check_infinite_scroll()
        
        if self.on_scroll:
            self.on_scroll()

    def on_mouse_wheel(self, event: tk.Event) -> None:
        """Handle mouse wheel scrolling."""
        if event.delta:
            delta = -1 * (event.delta // 120)
        else:
            delta = -1 if event.delta > 0 else 1
        
        self._last_scroll_direction = "down" if delta > 0 else "up"
        self._was_at_bottom_before_load = self.is_at_bottom(threshold=2)
        
        if self.canvas:
            self.canvas.yview_scroll(delta, 'units')
        
        self._check_infinite_scroll()
        if self.on_scroll:
            self.on_scroll()
        
        return "break"

    def on_linux_scroll(self, event: tk.Event) -> None:
        """Handle Linux mouse wheel scrolling."""
        delta = -1 if event.num == 4 else 1
        self._last_scroll_direction = "down" if delta > 0 else "up"
        self._was_at_bottom_before_load = self.is_at_bottom(threshold=2)
        
        if self.canvas:
            self.canvas.yview_scroll(delta, 'units')
        
        self._check_infinite_scroll()
        if self.on_scroll:
            self.on_scroll()
        
        return "break"

    def on_key_press(self, event: tk.Event) -> None:
        """Handle keyboard navigation."""
        # Implementation for arrow keys, page up/down, home/end
        # ... (keyboard navigation logic from original)
        return "break"

    def on_canvas_enter(self, event: tk.Event) -> None:
        """Handle mouse enter - grab focus."""
        if self.canvas:
            self.canvas.focus_set()

    def on_canvas_leave(self, event: tk.Event) -> None:
        """Handle mouse leave."""
        pass

    def scroll_to_index(self, index: int, total_items: int) -> bool:
        """Scroll to make index visible."""
        if not self.canvas or not (0 <= index < total_items):
            return False
            
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 0:
            return False
            
        item_top = index * self.item_height
        item_bottom = item_top + self.item_height
        total_height = total_items * self.item_height
        
        view_start = self._last_scroll_pos * total_height
        view_end = view_start + canvas_height
        
        if view_start <= item_top and item_bottom <= view_end:
            return True
            
        if item_top < view_start:
            target_pos = item_top / total_height
        else:
            target_pos = (item_bottom - canvas_height) / total_height
            
        target_pos = max(0.0, min(1.0, target_pos))
        
        if self.canvas:
            self.canvas.yview_moveto(target_pos)
        
        return True

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom."""
        if self.canvas:
            self.canvas.yview_moveto(1.0)

    def get_scroll_position(self) -> float:
        """Get current scroll position."""
        return self._last_scroll_pos

    def is_at_bottom(self, threshold: int = 5) -> bool:
        """Check if scrolled to bottom within threshold."""
        if not self.canvas:
            return True
            
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 0:
            return True
            
        last_visible = self._last_scroll_pos * self._get_item_count() + self._get_visible_item_count()
        return self._get_item_count() - last_visible <= threshold

    def _check_infinite_scroll(self) -> None:
        """Check if we need to load more items."""
        if not self.on_load_more:
            return
            
        current_time = time.time()
        if current_time - self._last_load_time < self._load_cooldown:
            return
            
        if self._last_scroll_direction != "down":
            return
            
        first_visible = self._last_scroll_pos * self._get_item_count()
        visible_count = self._get_visible_item_count()
        last_visible = first_visible + visible_count
        
        items_remaining = self._get_item_count() - last_visible
        
        if items_remaining <= self.load_threshold:
            self._last_load_time = current_time
            self.on_load_more()

    def _get_visible_item_count(self) -> int:
        """Calculate visible item count."""
        if not self.canvas:
            return 10
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 0:
            return 10
        return max(1, canvas_height // self.item_height)

    def _get_item_count(self) -> int:
        """Get item count from virtual list."""
        return len(self.virtual_list.items) if hasattr(self.virtual_list, 'items') else 0