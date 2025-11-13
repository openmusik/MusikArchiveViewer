"""
Widget Lifecycle and Pool Management System.

This class is responsible for creating, recycling, and managing the Tkinter widgets
displayed in the VirtualList, ensuring high performance with large datasets.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Deque
import weakref
from collections import deque

from .base import VirtualListItem
from ....utils.logging import get_logger

logger = get_logger(__name__)


class WidgetManager:
    """
    Manages a pool of recycled widgets to display virtual list items efficiently.
    """
    
    def __init__(self, virtual_list, item_height: int, max_pool_size: int = 50):
        self.virtual_list_ref = weakref.ref(virtual_list)
        self.item_height = item_height
        
        self.widget_pool: Deque[tk.Widget] = deque(maxlen=max_pool_size)
        self.visible_widgets: Dict[int, tk.Widget] = {}
        self._widget_to_index: Dict[int, int] = {}
        
        self.canvas: Optional[tk.Canvas] = None
        self.inner_frame: Optional[ttk.Frame] = None
        self._is_shutting_down: bool = False
        
        logger.debug(f"🚀 WidgetManager initialized (max_pool_size={max_pool_size})")

    @property
    def virtual_list(self):
        """Safely gets the VirtualList instance from the weak reference."""
        return self.virtual_list_ref()

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Sets the canvas on which widgets will be placed."""
        if self._is_shutting_down: return
        self.canvas = canvas
        logger.debug("✅ Canvas set for WidgetManager")

    def set_inner_frame(self, frame: ttk.Frame) -> None:
        """Sets the inner frame that holds all widgets."""
        if self._is_shutting_down: return
        self.inner_frame = frame
        logger.debug("✅ Inner frame set for WidgetManager")

    def get_or_create_widget(self, item: VirtualListItem) -> Optional[tk.Widget]:
        """Retrieves a recycled widget from the pool or creates a new one."""
        if self._is_shutting_down: return None
        
        # Try to get from pool
        while self.widget_pool:
            widget = self.widget_pool.popleft()
            try:
                if widget.winfo_exists():
                    logger.debug("🔥 Widget retrieved from pool.")
                    return widget
            except tk.TclError:
                continue
        
        # Create new widget - MUST be parented to inner_frame, not canvas
        try:
            if self.inner_frame and self.inner_frame.winfo_exists():
                # logger.debug("🆕 New widget created.")
                return item.create_widget(self.inner_frame)
        except Exception as e:
            logger.error(f"❌ Failed to create widget: {e}")
        return None

    def return_widget_to_pool(self, widget: tk.Widget, item: Optional[VirtualListItem] = None):
        """Hides a widget and returns it to the pool for reuse."""
        if self._is_shutting_down or not widget:
            return
        
        try:
            if not widget.winfo_exists():
                return
                
            widget.place_forget()
            
            # Call cleanup hook if available
            if item and hasattr(item, 'destroy_widget'):
                item.destroy_widget(widget)
            
            # Return to pool or destroy if pool is full
            if len(self.widget_pool) < self.widget_pool.maxlen:
                self.widget_pool.append(widget)
                # logger.debug("♻️ Widget returned to pool")
            else:
                widget.destroy()
                # logger.debug("🗑️ Widget destroyed (pool full)")
        except Exception as e:
            logger.debug(f"Error returning widget to pool: {e}")

    def clear_all_widgets(self):
        """Hides all visible widgets and completely clears the pool."""
        logger.debug("🧹 Clearing all widgets...")
        
        # Hide and pool all visible widgets
        for index, widget in list(self.visible_widgets.items()):
            item = None
            if self.virtual_list and index < len(self.virtual_list.items):
                item = self.virtual_list.items[index]
            self.return_widget_to_pool(widget, item)
        
        self.visible_widgets.clear()
        self._widget_to_index.clear()
        
        # Destroy all pooled widgets
        for widget in list(self.widget_pool):
            try:
                if widget.winfo_exists(): 
                    widget.destroy()
            except tk.TclError: 
                pass
        self.widget_pool.clear()
        
        logger.debug("✅ All widgets cleared.")

    def render_item_at_index(self, item: VirtualListItem, index: int, is_selected: bool):
        """Creates or updates and positions a single widget at a given index."""
        if self._is_shutting_down or not self.inner_frame:
            return

        # Get or create widget
        widget = self.visible_widgets.get(index)
        if not widget or not widget.winfo_exists():
            widget = self.get_or_create_widget(item)
            if not widget: 
                return
            self.visible_widgets[index] = widget
            self._widget_to_index[id(widget)] = index

        # Update widget content and appearance
        try:
            item.update_widget(widget, is_selected)
        except Exception as e:
            logger.error(f"❌ Error updating widget for index {index}: {e}")
            return

        # CRITICAL: Position widget at absolute coordinates within inner_frame
        # The inner_frame itself is inside the canvas and will scroll with it
        y_position = index * self.item_height
        canvas_width = self.canvas.winfo_width() if self.canvas and self.canvas.winfo_exists() else 400
        
        try:
            widget.place(
                x=0, 
                y=y_position,
                width=canvas_width, 
                height=self.item_height,
                anchor='nw'
            )
            # logger.debug(f"📍 Widget {index} placed at y={y_position}")
        except Exception as e:
            logger.error(f"❌ Error placing widget at index {index}: {e}")

    def hide_and_pool_item(self, index: int):
        """Removes a widget from view and returns it to the pool."""
        if index not in self.visible_widgets:
            return
            
        widget = self.visible_widgets.pop(index)
        widget_id = id(widget)
        
        if widget_id in self._widget_to_index:
            del self._widget_to_index[widget_id]
        
        item = None
        if self.virtual_list and index < len(self.virtual_list.items):
            item = self.virtual_list.items[index]
        
        self.return_widget_to_pool(widget, item)
        logger.debug(f"👻 Widget {index} hidden and pooled")
            
    def update_visible_widgets(self, items: List[VirtualListItem], start_idx: int, end_idx: int, selected_index: Optional[int]):
        """The main rendering loop called by VirtualList."""
        if self._is_shutting_down:
            return
        
        logger.debug(f"🎨 update_visible_widgets: {start_idx} to {end_idx}")
        
        # Calculate which widgets should be visible
        visible_indices = set(range(start_idx, end_idx))
        current_indices = set(self.visible_widgets.keys())

        # Remove widgets that are no longer visible
        to_remove = current_indices - visible_indices
        for idx in to_remove:
            self.hide_and_pool_item(idx)
        
        # Render visible widgets
        for idx in visible_indices:
            if idx < len(items):
                self.render_item_at_index(items[idx], idx, idx == selected_index)
        
        logger.debug(f"✅ Render complete: {len(visible_indices)} widgets visible, {len(to_remove)} removed")

    def update_widget_selection(self, index: int, is_selected: bool):
        """Updates the visual state of a single visible widget."""
        if self._is_shutting_down:
            return
            
        widget = self.visible_widgets.get(index)
        if not widget or not widget.winfo_exists():
            return
            
        if not self.virtual_list or index >= len(self.virtual_list.items):
            return
            
        try:
            self.virtual_list.items[index].update_widget(widget, is_selected)
            logger.debug(f"🔄 Widget {index} selection updated: {is_selected}")
        except Exception as e:
            logger.error(f"❌ Error updating widget selection for index {index}: {e}")

    def shutdown(self):
        """Cleans up all managed widgets."""
        if self._is_shutting_down: 
            return
        self._is_shutting_down = True
        logger.debug("🛑 Shutting down WidgetManager...")
        self.clear_all_widgets()
        logger.debug("✅ WidgetManager shutdown complete.")