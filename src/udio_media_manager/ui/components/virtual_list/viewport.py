"""
Enhanced Viewport Management and Rendering System
"""

import tkinter as tk
import time
from typing import Dict, Set, Optional, Callable, Tuple, List, Any
import weakref
from contextlib import contextmanager

# Fix import path
from udio_media_manager.utils.logging import get_logger
from .base import VirtualListItem

logger = get_logger(__name__)


class ViewportManager:
    """
    Enhanced viewport manager with performance optimizations, comprehensive
    error handling, and advanced rendering capabilities.
    """
    
    def __init__(self, virtual_list, item_height: int, buffer_items: int = 10):
        # Use weakref to prevent circular references
        self.virtual_list_ref = weakref.ref(virtual_list)
        self.item_height = item_height
        self.buffer_items = buffer_items
        
        # Performance tracking
        self._last_update_time: float = 0
        self._update_delay: float = 0.016  # ~60 FPS
        self._pending_update: bool = False
        self._update_scheduled: bool = False
        self._render_count: int = 0
        self._last_render_stats: Dict[str, Any] = {}
        
        # State management
        self.visible_widgets: Dict[int, tk.Widget] = {}
        self._visible_range: Tuple[int, int] = (0, 0)
        self._last_canvas_size: Tuple[int, int] = (0, 0)
        self._shutdown: bool = False
        
        # UI references
        self.canvas: Optional[tk.Canvas] = None
        self._canvas_width: int = 400
        self._canvas_height: int = 300
        
        # Callbacks
        self.on_selection_change: Optional[Callable[[int], None]] = None
        self.on_viewport_change: Optional[Callable[[int, int], None]] = None
        
        # Performance optimizations
        self._batch_updates: bool = True
        self._min_visible_change: int = 5  # Minimum change to trigger update
        self._last_visible_set: Set[int] = set()
        
        logger.debug(f"🚀 ViewportManager initialized (item_height={item_height}, buffer={buffer_items})")

    @property
    def virtual_list(self):
        """Safely get the virtual list reference."""
        return self.virtual_list_ref() if self.virtual_list_ref else None

    def set_canvas(self, canvas: tk.Canvas) -> None:
        """Set canvas reference with comprehensive setup."""
        try:
            if self._shutdown:
                return
                
            self.canvas = canvas
            self._update_canvas_dimensions()
            
            # Set up canvas bindings
            if canvas and canvas.winfo_exists():
                canvas.bind('<Configure>', self._on_canvas_configure_enhanced)
                
            logger.debug("✅ Canvas set for ViewportManager")
            
        except Exception as e:
            logger.error(f"❌ Failed to set canvas: {e}")

    def get_visible_range(self) -> Tuple[int, int]:
        """
        Calculate the visible item range with comprehensive error handling.
        Returns (start_index, end_index) tuple.
        """
        if self._shutdown or not self.canvas or not self.canvas.winfo_exists():
            return 0, 0
            
        try:
            # Get current canvas state
            self._update_canvas_dimensions()
            if self._canvas_height <= 0:
                return 0, 0
            
            # Get scroll position safely
            scroll_pos = self._get_safe_scroll_position()
            
            # Calculate visible range with buffer
            total_items = len(self.virtual_list.items) if self.virtual_list and hasattr(self.virtual_list, 'items') else 0
            if total_items == 0:
                return 0, 0
                
            # Calculate items per page
            items_per_page = max(1, self._canvas_height // self.item_height)
            
            # Calculate start and end indices
            start_idx = max(0, int(scroll_pos * total_items) - self.buffer_items)
            end_idx = min(total_items, start_idx + items_per_page + (2 * self.buffer_items))
            
            # Ensure valid range
            start_idx = max(0, start_idx)
            end_idx = min(total_items, end_idx)
            
            # Only update if there's a significant change
            current_range = (start_idx, end_idx)
            last_range = self._visible_range
            
            if (abs(current_range[0] - last_range[0]) > self._min_visible_change or
                abs(current_range[1] - last_range[1]) > self._min_visible_change):
                self._visible_range = current_range
                
                # Notify about viewport change
                if self.on_viewport_change and current_range != last_range:
                    self.on_viewport_change(current_range[0], current_range[1])
            
            return current_range
            
        except Exception as e:
            logger.debug(f"Visible range calculation error: {e}")
            return 0, 0

    def get_canvas_width(self) -> int:
        """Get current canvas width with error handling."""
        try:
            if self.canvas and self.canvas.winfo_exists():
                return self.canvas.winfo_width()
            return self._canvas_width
        except Exception:
            return self._canvas_width

    def on_canvas_configure(self, event: tk.Event) -> None:
        """Enhanced canvas configuration handler."""
        try:
            if self._shutdown:
                return
                
            old_width, old_height = self._canvas_width, self._canvas_height
            self._canvas_width = event.width
            self._canvas_height = event.height
            
            # Only trigger update if size changed significantly
            if (abs(old_width - event.width) > 10 or 
                abs(old_height - event.height) > 10):
                logger.debug(f"📐 Canvas resized to {event.width}x{event.height}")
                self.schedule_update(immediate=True)
                
        except Exception as e:
            logger.error(f"❌ Canvas configure error: {e}")

    def _on_canvas_configure_enhanced(self, event: tk.Event) -> None:
        """Enhanced canvas configuration with performance optimizations."""
        with self._update_context("canvas_configure"):
            self.on_canvas_configure(event)

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle canvas clicks with comprehensive error handling."""
        try:
            if self._shutdown:
                return
                
            item_index = self._get_item_at_position_enhanced(event.x, event.y)
            if item_index is not None and self.on_selection_change:
                self.on_selection_change(item_index)
                
        except Exception as e:
            logger.debug(f"Canvas click handling error: {e}")

    def on_canvas_double_click(self, event: tk.Event) -> None:
        """Handle canvas double-clicks with error handling."""
        try:
            if self._shutdown:
                return
                
            item_index = self._get_item_at_position_enhanced(event.x, event.y)
            if (item_index is not None and self.virtual_list and 
                hasattr(self.virtual_list, 'on_double_click')):
                self.virtual_list.on_double_click(item_index)
                
        except Exception as e:
            logger.debug(f"Canvas double-click handling error: {e}")

    def schedule_update(self, immediate: bool = False) -> None:
        """Schedule viewport update with performance optimizations."""
        if self._shutdown:
            return
            
        current_time = time.time()
        
        if immediate:
            self._perform_update()
        elif current_time - self._last_update_time >= self._update_delay:
            self._perform_update()
        elif not self._pending_update:
            self._pending_update = True
            if not self._update_scheduled:
                self._update_scheduled = True
                delay_ms = max(1, int(self._update_delay * 1000))
                if self.virtual_list:
                    self.virtual_list.after(delay_ms, self._perform_scheduled_update)

    def _perform_update(self) -> None:
        """Perform the actual viewport update."""
        with self._update_context("viewport_update"):
            self._last_update_time = time.time()
            self._update_visible_items_enhanced()
            self._pending_update = False
            self._update_scheduled = False

    def _perform_scheduled_update(self) -> None:
        """Perform scheduled update with state management."""
        if self._pending_update and not self._shutdown:
            self._perform_update()

    def refresh_item(self, index: int) -> bool:
        """Refresh specific item if visible with error handling."""
        try:
            if (self._shutdown or index not in self.visible_widgets or 
                not self.virtual_list or index >= len(self.virtual_list.items)):
                return False
                
            widget = self.visible_widgets[index]
            selected_index = getattr(self.virtual_list, 'selected_index', None)
            
            # Use context manager for safe widget update
            with self._widget_update_context(widget, index):
                self.virtual_list.items[index].update_widget(widget, index == selected_index)
                
            return True
            
        except Exception as e:
            logger.debug(f"Item refresh error for index {index}: {e}")
            return False

    def select_item(self, index: int) -> bool:
        """Select item by index with comprehensive validation."""
        try:
            if (self._shutdown or not self.virtual_list or 
                not (0 <= index < len(self.virtual_list.items))):
                return False
                
            if self.on_selection_change:
                self.on_selection_change(index)
                # Refresh the item to show selection state
                self.refresh_item(index)
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Item selection error for index {index}: {e}")
            return False

    def update_visible_widgets(self, start_idx: int, end_idx: int, selected_index: Optional[int] = None) -> None:
        """
        Enhanced method to update visible widgets in the specified range.
        """
        if self._shutdown or not self.virtual_list:
            return
            
        try:
            visible_indices = set(range(start_idx, end_idx))
            current_indices = set(self.visible_widgets.keys())
            
            # Calculate changes
            to_remove = current_indices - visible_indices
            to_add = visible_indices - current_indices
            to_update = visible_indices & current_indices
            
            # Remove widgets no longer visible
            self._remove_widgets(to_remove)
            
            # Add new widgets
            self._add_widgets(to_add, selected_index)
            
            # Update existing widgets
            self._update_widgets(to_update, selected_index)
            
            # Update statistics
            self._update_render_stats(len(visible_indices), len(to_add), len(to_remove))
            
        except Exception as e:
            logger.error(f"❌ Error updating visible widgets: {e}")

    def shutdown(self) -> None:
        """Comprehensive cleanup with resource management."""
        if self._shutdown:
            return
            
        self._shutdown = True
        logger.debug("🛑 Shutting down ViewportManager...")
        
        try:
            # Clear all visible widgets
            widget_manager = getattr(self.virtual_list, 'widget_manager', None) if self.virtual_list else None
            
            for index, widget in list(self.visible_widgets.items()):
                try:
                    if widget_manager and widget.winfo_exists():
                        item = (self.virtual_list.items[index] 
                                if self.virtual_list and index < len(self.virtual_list.items) 
                                else None)
                        widget_manager.return_widget_to_pool(widget, item)
                    elif widget.winfo_exists():
                        widget.destroy()
                except Exception as e:
                    logger.debug(f"Widget cleanup error: {e}")
            
            self.visible_widgets.clear()
            self._last_visible_set.clear()
            
            # Clear references
            self.canvas = None
            self.on_selection_change = None
            self.on_viewport_change = None
            
            logger.debug("✅ ViewportManager shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during ViewportManager shutdown: {e}")

    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering statistics for performance monitoring."""
        return self._last_render_stats.copy()

    # ===== PRIVATE METHODS =====

    def _update_visible_items_enhanced(self) -> None:
        """Enhanced visible items update with performance optimizations."""
        if (self._shutdown or not self.canvas or not self.canvas.winfo_exists() or 
            not self.virtual_list or not hasattr(self.virtual_list, 'items')):
            return

        try:
            # Get visible range
            start_idx, end_idx = self.get_visible_range()
            if start_idx >= end_idx:
                return
                
            # Update widgets in the visible range
            selected_index = getattr(self.virtual_list, 'selected_index', None)
            self.update_visible_widgets(start_idx, end_idx, selected_index)
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced visible items update: {e}")

    def _remove_widgets(self, indices: Set[int]) -> None:
        """Remove widgets from the specified indices."""
        widget_manager = getattr(self.virtual_list, 'widget_manager', None) if self.virtual_list else None
        
        for idx in indices:
            if idx in self.visible_widgets:
                widget = self.visible_widgets.pop(idx)
                try:
                    if widget_manager and widget.winfo_exists():
                        item = (self.virtual_list.items[idx] 
                                if idx < len(self.virtual_list.items) 
                                else None)
                        widget_manager.return_widget_to_pool(widget, item)
                except Exception as e:
                    logger.debug(f"Widget removal error for index {idx}: {e}")

    def _add_widgets(self, indices: Set[int], selected_index: Optional[int]) -> None:
        """Add widgets for the specified indices."""
        if not self.virtual_list or not self.canvas:
            return
            
        widget_manager = getattr(self.virtual_list, 'widget_manager', None)
        if not widget_manager:
            return
            
        for idx in indices:
            if idx < len(self.virtual_list.items):
                try:
                    item = self.virtual_list.items[idx]
                    widget = widget_manager.get_or_create_widget(item)
                    
                    # Update widget state
                    item.update_widget(widget, idx == selected_index)
                    
                    # Position widget
                    y_pos = idx * self.item_height
                    widget.place(
                        x=0, 
                        y=y_pos, 
                        width=self._canvas_width, 
                        height=self.item_height
                    )
                    
                    self.visible_widgets[idx] = widget
                    self._bind_interactions_enhanced(widget, idx)
                    
                except Exception as e:
                    logger.debug(f"Widget creation error for index {idx}: {e}")

    def _update_widgets(self, indices: Set[int], selected_index: Optional[int]) -> None:
        """Update existing widgets."""
        if not self.virtual_list:
            return
            
        for idx in indices:
            if idx in self.visible_widgets and idx < len(self.virtual_list.items):
                try:
                    widget = self.visible_widgets[idx]
                    item = self.virtual_list.items[idx]
                    item.update_widget(widget, idx == selected_index)
                except Exception as e:
                    logger.debug(f"Widget update error for index {idx}: {e}")

    def _get_item_at_position_enhanced(self, x: int, y: int) -> Optional[int]:
        """Enhanced item position detection."""
        if not self.canvas or not self.virtual_list or not hasattr(self.virtual_list, 'items'):
            return None
            
        try:
            canvas_y = self.canvas.canvasy(y)
            item_index = int(canvas_y // self.item_height)
            
            if 0 <= item_index < len(self.virtual_list.items):
                # Verify the click is within the item bounds
                item_top = item_index * self.item_height
                item_bottom = item_top + self.item_height
                
                if item_top <= canvas_y < item_bottom:
                    return item_index
                    
        except (ValueError, ZeroDivisionError, tk.TclError):
            pass
            
        return None

    def _bind_interactions_enhanced(self, widget: tk.Widget, index: int) -> None:
        """Enhanced interaction binding with error handling."""
        try:
            if not widget.winfo_exists():
                return
                
            # Create custom bind tag for virtual list interactions
            bind_tags = list(widget.bindtags())
            custom_tag = f"VirtualListBindings_{id(self)}"
            
            if custom_tag not in bind_tags:
                bind_tags.insert(1, custom_tag)
                widget.bindtags(tuple(bind_tags))
            
            # Bind click event
            widget.bind('<Button-1>', 
                       lambda e, i=index: self._on_widget_click_enhanced(i), 
                       add='+')
            
            # Recursively bind children
            for child in widget.winfo_children():
                self._bind_interactions_enhanced(child, index)
                
        except Exception as e:
            logger.debug(f"Interaction binding error: {e}")

    def _on_widget_click_enhanced(self, index: int) -> None:
        """Enhanced widget click handler."""
        try:
            if not self._shutdown and self.on_selection_change:
                self.on_selection_change(index)
        except Exception as e:
            logger.debug(f"Widget click handling error: {e}")

    def _update_canvas_dimensions(self) -> None:
        """Update canvas dimensions safely."""
        try:
            if self.canvas and self.canvas.winfo_exists():
                self._canvas_width = self.canvas.winfo_width()
                self._canvas_height = self.canvas.winfo_height()
        except Exception:
            pass

    def _get_safe_scroll_position(self) -> float:
        """Get scroll position with error handling."""
        try:
            if self.canvas and self.canvas.winfo_exists():
                bbox = self.canvas.bbox('all')
                if bbox:
                    total_height = bbox[3]
                    visible_top = self.canvas.canvasy(0)
                    return visible_top / total_height if total_height > 0 else 0.0
        except Exception:
            pass
        return 0.0

    def _update_render_stats(self, visible_count: int, added: int, removed: int) -> None:
        """Update rendering statistics."""
        self._render_count += 1
        self._last_render_stats = {
            'visible_count': visible_count,
            'widgets_added': added,
            'widgets_removed': removed,
            'total_renders': self._render_count,
            'timestamp': time.time()
        }

    @contextmanager
    def _update_context(self, operation: str):
        """Context manager for update operations."""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            logger.error(f"❌ Error in {operation}: {e}")
        finally:
            duration = time.time() - start_time
            if duration > 0.1:  # Log slow operations
                logger.warning(f"🐢 Slow {operation}: {duration:.3f}s")

    @contextmanager
    def _widget_update_context(self, widget: tk.Widget, index: int):
        """Context manager for widget updates."""
        try:
            if widget.winfo_exists():
                yield
        except Exception as e:
            logger.debug(f"Widget update context error for index {index}: {e}")

    def __del__(self):
        """Destructor for cleanup."""
        try:
            if not self._shutdown:
                self.shutdown()
        except:
            pass