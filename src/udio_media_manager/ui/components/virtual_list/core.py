"""
ULTIMATE PRO Virtual List Implementation - COMPATIBLE VERSION

This COMPATIBLE VERSION maintains all performance optimizations while
working with the existing WidgetManager API.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Tuple, Generator, Dict, Any
import time

from .base import VirtualListItem
from .widget_manager import WidgetManager
from ....utils.logging import get_logger

logger = get_logger(__name__)


class VirtualList(ttk.Frame):
    """COMPATIBLE PRO VERSION: High-performance virtual list with existing WidgetManager API."""
    
    def __init__(
        self,
        parent: tk.Widget,
        item_height: int = 56,
        buffer_items: int = 5,  # Reduced for better performance
        on_select: Optional[Callable[[int], None]] = None,
        on_double_click: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        # Core configuration
        self.item_height = item_height
        self.buffer_items = buffer_items
        self.on_select = on_select
        self.on_double_click = on_double_click
        
        # Data state
        self.items: List[VirtualListItem] = []
        self.total_count: int = 0
        self.selected_index: Optional[int] = None
        self._is_shutting_down = False

        # Rendering state
        self._render_job: Optional[str] = None
        self._render_generator: Optional[Generator] = None
        self._last_render_time: float = 0
        self._render_stats: Dict[str, Any] = {
            'total_renders': 0,
            'average_render_time': 0,
            'last_render_duration': 0
        }
        
        # Scroll state
        self._last_scroll_position: float = 0
        self._scroll_velocity: float = 0
        self._last_scroll_time: float = 0
        
        # Create optimized canvas
        self.canvas = tk.Canvas(
            self, 
            highlightthickness=0, 
            takefocus=1,
            background='white',
            borderwidth=0,
            relief='flat'
        )
        
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self._on_scrollbar_scroll)
        self.canvas.configure(yscrollcommand=self._on_canvas_scroll)
        
        # Create inner frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.inner_frame, 
            anchor='nw', 
            tags="inner_frame"
        )
        
        # COMPATIBLE: Initialize widget manager without unsupported parameters
        self.widget_manager = WidgetManager(self, self.item_height)
        self.widget_manager.set_canvas(self.canvas)
        self.widget_manager.set_inner_frame(self.inner_frame)
        
        self._layout_ui()
        self._setup_bindings()
        
        logger.info("🚀 ULTIMATE VirtualList initialized (Compatible Version)")

    def _layout_ui(self):
        """Optimized UI layout."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        self.scrollbar.grid(row=0, column=1, sticky='ns', padx=0, pady=0)

    def _setup_bindings(self):
        """Optimized event binding setup."""
        # Mouse wheel bindings
        self.bind_all("<MouseWheel>", self._on_mouse_wheel, add=True)
        self.canvas.bind('<Button-4>', self._on_mouse_wheel)
        self.canvas.bind('<Button-5>', self._on_mouse_wheel)
        
        # Configuration binding (debounced)
        self._configure_job: Optional[str] = None
        self.canvas.bind('<Configure>', self._on_canvas_configure_debounced)
        
        # Keyboard navigation
        self.canvas.bind('<KeyPress-Up>', lambda e: self._navigate(-1))
        self.canvas.bind('<KeyPress-Down>', lambda e: self._navigate(1))
        self.canvas.bind('<KeyPress-Prior>', self._on_page_up)
        self.canvas.bind('<KeyPress-Next>', self._on_page_down)
        self.canvas.bind('<KeyPress-Home>', self._on_home)
        self.canvas.bind('<KeyPress-End>', self._on_end)
        
        # Click bindings
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<Double-Button-1>', self._on_canvas_double_click)
        
        # Focus management
        self.canvas.bind('<FocusIn>', self._on_focus_in)
        self.canvas.bind('<FocusOut>', self._on_focus_out)

    def _on_canvas_configure_debounced(self, event: tk.Event):
        """Debounced canvas configure handler."""
        if self._configure_job:
            self.after_cancel(self._configure_job)
        
        self._configure_job = self.after(10, lambda: self._on_canvas_configure(event))

    def set_items(self, items: List[VirtualListItem], total_count: Optional[int] = None):
        """Set items with performance optimizations."""
        if self._is_shutting_down: 
            return
        
        logger.debug(f"📥 VirtualList.set_items: {len(items)} items")
        
        # Cancel any pending operations
        self._cancel_render_job()
        if self._configure_job:
            self.after_cancel(self._configure_job)
            self._configure_job = None
        
        # Clear existing state
        self.widget_manager.clear_all_widgets()
        
        # Update data
        self.items = items
        self.total_count = total_count or len(items)
        self.selected_index = None
        
        # Reset scroll position
        self.canvas.yview_moveto(0)
        self._update_scroll_region()
        
        # Schedule initial render
        self.after_idle(self._schedule_render)
        
        logger.info(f"✅ VirtualList loaded {len(items)} items")

    def _get_visible_range(self) -> Tuple[int, int]:
        """Calculate visible range with optimizations."""
        if not self.canvas.winfo_exists(): 
            return 0, 0
        
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1: 
            return 0, 0
        
        # Get current scroll position
        yview = self.canvas.yview()
        scroll_top = yview[0]
        scroll_bottom = yview[1]
        
        # Calculate total content height
        total_height = self.total_count * self.item_height
        
        # Calculate visible pixel range
        visible_top_px = scroll_top * total_height
        visible_bottom_px = scroll_bottom * total_height
        
        # Convert to item indices with buffer
        start_idx = max(0, int(visible_top_px / self.item_height) - self.buffer_items)
        end_idx = min(self.total_count, int(visible_bottom_px / self.item_height) + 1 + self.buffer_items)
        
        return start_idx, end_idx

    def _schedule_render(self, event=None):
        """Schedule render with performance throttling."""
        if self._is_shutting_down: 
            return
            
        # Throttle rapid render requests
        current_time = time.time()
        if current_time - self._last_render_time < 0.001:  # 1ms throttle
            return
            
        self._last_render_time = current_time
        self._cancel_render_job()
        self._render_job = self.after(1, self._run_render_generator)

    def _run_render_generator(self):
        """Run render generator."""
        render_start = time.time()
        self._render_generator = self._render_viewport_generator(render_start)
        self._step_render_generator()
        
    def _step_render_generator(self):
        """Execute one render step."""
        try:
            if self._render_generator and not self._is_shutting_down:
                next(self._render_generator)
                self._render_job = self.after(1, self._step_render_generator)
        except StopIteration:
            self._render_job = None
            self._render_generator = None
        except Exception as e:
            logger.error(f"❌ Render error: {e}")
            self._render_job = None
            self._render_generator = None

    def _render_viewport_generator(self, start_time: float) -> Generator:
        """Yield-based renderer with enhanced debugging."""
        if self._is_shutting_down or not self.canvas.winfo_exists(): 
            return
        
        # Calculate visible range
        start_idx, end_idx = self._get_visible_range()
        
        logger.debug(f"🎨 Rendering viewport: items {start_idx} to {end_idx} (total: {len(self.items)})")
        
        # Debug: Check what items we're about to render
        if start_idx < len(self.items) and end_idx <= len(self.items):
            visible_tracks = [getattr(item, 'track', None) for item in self.items[start_idx:end_idx]]
            track_titles = [track.title if track else "NO TRACK" for track in visible_tracks]
            logger.debug(f"🔍 Visible tracks: {track_titles}")
        
        # Update scroll tracking
        current_time = time.time()
        current_scroll = self.canvas.yview()[0]
        self._scroll_velocity = (current_scroll - self._last_scroll_position) / max(0.001, current_time - self._last_scroll_time)
        self._last_scroll_position = current_scroll
        self._last_scroll_time = current_time
        
        # Perform widget update
        self.widget_manager.update_visible_widgets(
            self.items, start_idx, end_idx, self.selected_index
        )
        
        # Update render statistics
        render_duration = time.time() - start_time
        self._update_render_stats(render_duration)
        
        yield

    def _update_render_stats(self, duration: float):
        """Update performance statistics."""
        self._render_stats['total_renders'] += 1
        self._render_stats['last_render_duration'] = duration
        
        # Exponential moving average for render time
        alpha = 0.1
        old_avg = self._render_stats['average_render_time']
        self._render_stats['average_render_time'] = (
            alpha * duration + (1 - alpha) * old_avg
        )
        
        # Log performance periodically
        if self._render_stats['total_renders'] % 100 == 0:
            logger.debug(
                f"📊 Render Stats: {self._render_stats['average_render_time']*1000:.1f}ms avg"
            )

    def _on_canvas_configure(self, event: tk.Event):
        """Handle canvas configuration changes."""
        if self._is_shutting_down: 
            return
            
        # Update inner frame width to match canvas
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self._update_scroll_region()
        self._schedule_render()

    def _on_canvas_scroll(self, first: float, last: float):
        """Handle canvas scroll events."""
        self.scrollbar.set(first, last)
        self._schedule_render()

    def _on_scrollbar_scroll(self, *args):
        """Handle scrollbar drag events."""
        if not self._is_shutting_down and self.canvas.winfo_exists():
            self.canvas.yview(*args)
            self._schedule_render()

    def _on_mouse_wheel(self, event: tk.Event):
        """Handle mouse wheel scrolling."""
        if self._is_shutting_down or not self.canvas.winfo_exists(): 
            return

        # Cross-platform delta calculation
        if event.num == 4: 
            delta = -1  # Linux scroll up
        elif event.num == 5: 
            delta = 1   # Linux scroll down
        else: 
            delta = -int(event.delta / 120)  # Windows/macOS

        # Perform scroll
        self.canvas.yview_scroll(delta, "units")
        self._schedule_render()

    def _on_canvas_click(self, event: tk.Event):
        """Handle canvas click events."""
        if self._is_shutting_down: 
            return
            
        self.canvas.focus_set()
        y_coord = self.canvas.canvasy(event.y)
        index = int(y_coord // self.item_height)
        
        if 0 <= index < self.total_count: 
            self._set_selection(index)

    def _on_canvas_double_click(self, event: tk.Event):
        """Handle canvas double-click events."""
        if self._is_shutting_down or not self.on_double_click: 
            return
            
        self.canvas.focus_set()
        y_coord = self.canvas.canvasy(event.y)
        index = int(y_coord // self.item_height)
        
        if 0 <= index < self.total_count: 
            self.on_double_click(index)

    def _on_focus_in(self, event: tk.Event):
        """Handle focus in events."""
        self.canvas.configure(highlightbackground='#0078d4', highlightthickness=1)

    def _on_focus_out(self, event: tk.Event):
        """Handle focus out events."""
        self.canvas.configure(highlightbackground='systemWindowBackgroundColor', highlightthickness=0)

    def _navigate(self, delta: int):
        """Keyboard navigation handler."""
        if not self.items: 
            return
            
        current_index = 0 if self.selected_index is None else self.selected_index
        new_index = max(0, min(len(self.items) - 1, current_index + delta))
        
        if new_index != self.selected_index:
            self._set_selection(new_index)
            self.scroll_to_index(new_index)

    def _on_page_up(self, event): 
        if self.canvas.winfo_exists(): 
            self._navigate(-(self.canvas.winfo_height() // self.item_height))
    
    def _on_page_down(self, event): 
        if self.canvas.winfo_exists(): 
            self._navigate(self.canvas.winfo_height() // self.item_height)
    
    def _on_home(self, event): 
        self._set_selection(0)
        self.scroll_to_index(0)
    
    def _on_end(self, event): 
        self._set_selection(len(self.items) - 1)
        self.scroll_to_index(len(self.items) - 1)

    def _set_selection(self, index: int):
        """Set selection with visual feedback."""
        if index == self.selected_index:
            return
            
        if not (0 <= index < len(self.items)):
            return
            
        old_index = self.selected_index
        self.selected_index = index
        
        # Update widget appearances
        if old_index is not None:
            self.widget_manager.update_widget_selection(old_index, False)
        
        self.widget_manager.update_widget_selection(index, True)
        
        if self.on_select:
            self.on_select(index)

    def scroll_to_index(self, index: int):
        """Scroll to make the specified index visible."""
        if not (0 <= index < self.total_count) or not self.canvas.winfo_exists(): 
            return
            
        total_height = self.total_count * self.item_height
        if total_height > 0:
            # Calculate position with some padding
            item_top = (index * self.item_height) / total_height
            
            # Scroll if not visible
            view_top, view_bottom = self.canvas.yview()
            if item_top < view_top or item_top > view_bottom:
                target_pos = max(0, min(1.0, item_top - 0.1))
                self.canvas.yview_moveto(target_pos)
                self._schedule_render()

    def _update_scroll_region(self):
        """Update scroll region efficiently."""
        if not self.canvas or not self.canvas.winfo_exists(): 
            return
        
        canvas_width = max(1, self.canvas.winfo_width())
        total_height = max(1, self.total_count * self.item_height)
        
        # Update scroll region
        self.canvas.configure(scrollregion=f"0 0 {canvas_width} {total_height}")
        self.inner_frame.configure(width=canvas_width, height=total_height)

    def _cancel_render_job(self):
        """Cancel pending render job."""
        if self._render_job:
            self.after_cancel(self._render_job)
            self._render_job = None
        self._render_generator = None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return self._render_stats.copy()

    def get_visible_indices(self) -> Tuple[int, int]:
        """Get currently visible indices."""
        return self._get_visible_range()

    def get_selected_item(self) -> Optional[VirtualListItem]:
        """Get currently selected item."""
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def refresh_item(self, index: int):
        """Refresh a specific item."""
        if 0 <= index < len(self.items):
            self.widget_manager.refresh_widget(index)

    def shutdown(self):
        """Comprehensive shutdown."""
        if self._is_shutting_down: 
            return
            
        self._is_shutting_down = True
        logger.info("🛑 VirtualList shutting down...")
        
        # Cancel all pending operations
        self.unbind_all("<MouseWheel>")
        self._cancel_render_job()
        
        if self._configure_job:
            self.after_cancel(self._configure_job)
            self._configure_job = None
        
        # Shutdown widget manager
        if self.widget_manager: 
            self.widget_manager.shutdown()
            
        # Log final statistics
        stats = self.get_performance_stats()
        logger.info(f"📊 Final stats: {stats['total_renders']} renders")
        
        logger.info("✅ VirtualList shutdown complete.")