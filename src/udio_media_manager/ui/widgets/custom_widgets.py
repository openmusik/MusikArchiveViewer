# udio_media_manager/ui/widgets/custom_widgets.py - FULLY UPGRADED & CLEANED

"""
Custom, Low-Level UI Widgets for the Udio Media Manager.

This module provides a suite of reusable, theme-aware Tkinter widgets. These
are foundational building blocks and do not contain application business logic.
High-level components like the VirtualList have been moved to the `ui/components`
package to ensure a clean separation of concerns.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Dict, Any

from PIL import Image, ImageTk

from ...core.constants import THUMBNAIL_SIZE
from ...utils.logging import get_logger
from ..themes.theme_manager import ThemeManager

logger = get_logger(__name__)


# ==============================================================================
# WIDGET: ToolTip
# ==============================================================================
class ToolTip:
    """Creates a theme-aware tooltip for a given widget with a configurable delay."""
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.show_job_id: Optional[str] = None

        self.widget.bind("<Enter>", self.schedule_show, add='+')
        self.widget.bind("<Leave>", self.cancel_show, add='+')
        self.widget.bind("<Destroy>", self._on_destroy, add='+')

    def schedule_show(self, event: Any) -> None:
        """Schedules the tooltip to appear after a delay."""
        self.cancel_show()
        self.show_job_id = self.widget.after(self.delay, self.show_tooltip)

    def cancel_show(self, event: Any = None) -> None:
        """Cancels the scheduled appearance and hides any visible tooltip."""
        if self.show_job_id:
            self.widget.after_cancel(self.show_job_id)
            self.show_job_id = None
        self.hide_tooltip()

    def show_tooltip(self) -> None:
        """Displays the tooltip window at the cursor's current position."""
        if self.tooltip_window or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_pointerx() + 20
        y = self.widget.winfo_pointery() + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self.tooltip_window, text=self.text, justify='left', style="Tooltip.TLabel")
        label.pack(ipadx=5, ipady=3)

    def hide_tooltip(self, event: Any = None) -> None:
        """Destroys the tooltip window if it exists."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

    def _on_destroy(self, event: Any) -> None:
        """Cleans up bindings when the parent widget is destroyed."""
        self.hide_tooltip()
        # No need to unbind; the widget is being destroyed anyway.

# ==============================================================================
# WIDGET: ClickableLabel
# ==============================================================================
class ClickableLabel(ttk.Label):
    """A label that acts like a hyperlink, with hover effects managed by its style."""
    def __init__(self, parent, text: str, command: Optional[Callable] = None, **kwargs):
        kwargs.setdefault('style', 'Link.TLabel')
        super().__init__(parent, text=text, cursor="hand2", **kwargs)
        self.command = command
        if self.command:
            self.bind("<Button-1>", self._on_click)

    def _on_click(self, event: Any) -> None:
        """Executes the command when the label is clicked."""
        if self.command:
            self.command()

# ==============================================================================
# WIDGET: SearchEntry with Debouncing
# ==============================================================================
class SearchEntry(ttk.Frame):
    """An entry widget with a placeholder, a clear button, and search debouncing."""
    def __init__(self, parent, on_search: Callable[[str], None], on_clear: Callable[[], None], placeholder: str = "Search...", debounce_ms: int = 300):
        super().__init__(parent)
        self.on_search = on_search
        self.on_clear = on_clear
        self.placeholder_text = placeholder
        self.debounce_ms = debounce_ms
        self._debounce_job: Optional[str] = None

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_text_change_debounced)

        self.entry = ttk.Entry(self, textvariable=self.search_var, width=40, style="Search.TEntry")
        self.entry.pack(side="left", fill="x", expand=True, ipady=2, padx=(1,0))
        self.clear_button = ttk.Label(self, text="×", style="ClearButton.TLabel", cursor="hand2")
        self.clear_button.bind("<Button-1>", self._clear_search)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", lambda e: self._trigger_search_now())
        self.entry.bind("<KP_Enter>", lambda e: self._trigger_search_now())

        self._set_placeholder_if_empty()
        self._toggle_clear_button()

    def _set_placeholder_if_empty(self):
        if not self.search_var.get():
            self.entry.insert(0, self.placeholder_text)
            self.entry.config(style="Placeholder.TEntry")

    def _clear_placeholder(self):
        if self.search_var.get() == self.placeholder_text:
            self.entry.delete(0, "end")
            self.entry.config(style="Search.TEntry")

    def _on_focus_in(self, event: Any): self._clear_placeholder()
    def _on_focus_out(self, event: Any): self._set_placeholder_if_empty()

    def _on_text_change_debounced(self, *args):
        """Schedules a search after the user stops typing."""
        self._toggle_clear_button()
        if self._debounce_job: self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self.debounce_ms, self._trigger_search_now)

    def _trigger_search_now(self):
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
            self._debounce_job = None
        self.on_search(self.get_value())

    def _toggle_clear_button(self):
        show = self.get_value() != ""
        if show and not self.clear_button.winfo_ismapped():
            self.clear_button.pack(side="right", padx=(5, 5))
        elif not show and self.clear_button.winfo_ismapped():
            self.clear_button.pack_forget()

    def _clear_search(self, event: Any = None):
        self.search_var.set("")
        self._set_placeholder_if_empty()
        self.entry.focus_set()
        self.on_clear()

    def focus_search(self):
        self.entry.focus_set()
        self._on_focus_in(None)
        self.entry.select_range(0, 'end')

    def get_value(self) -> str:
        """Returns the current text value, excluding the placeholder."""
        current_text = self.search_var.get()
        return "" if current_text == self.placeholder_text else current_text.strip()

# ==============================================================================
# WIDGET: StatusBar
# ==============================================================================
class StatusBar(ttk.Frame):
    """A status bar for the bottom of the window to show messages and progress."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="StatusBar.TFrame", padding=(10, 5), **kwargs)
        self.message_var = tk.StringVar(value="Ready")
        self.message_label = ttk.Label(self, textvariable=self.message_var, anchor="w")
        self.message_label.pack(side="left", fill="x", expand=True)
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=150, mode="determinate")
        self.show_progress(False)

    def set_message(self, message: str, level: str = "info"):
        self.message_var.set(message)
        style_map = {"success": "Success.Status.TLabel", "warning": "Warning.Status.TLabel", "error": "Error.Status.TLabel"}
        self.message_label.config(style=style_map.get(level, "Status.TLabel"))

    def show_progress(self, show: bool = True):
        if show and not self.progress_bar.winfo_ismapped():
            self.progress_bar.pack(side="right", padx=(10, 0))
        elif not show and self.progress_bar.winfo_ismapped():
            self.progress_bar.pack_forget()

    def update_progress(self, value: float, message: Optional[str] = None):
        self.progress_bar['value'] = value
        if message: self.message_var.set(f"{message} ({value:.0f}%)")

# ==============================================================================
# WIDGET: ThumbnailLabel
# ==============================================================================
class ThumbnailLabel(ttk.Label):
    """A label for displaying track thumbnails with a themed placeholder."""
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        super().__init__(parent, style="Thumbnail.TLabel", **kwargs)
        self.theme = theme_manager
        self.photo: Optional[ImageTk.PhotoImage] = None
        self._create_placeholder()

    def _create_placeholder(self):
        """Creates a default placeholder image based on the current theme."""
        try:
            placeholder_color = self.theme.current_colors.tertiary_bg
            img = Image.new('RGB', THUMBNAIL_SIZE, color=placeholder_color)
            self.photo = ImageTk.PhotoImage(img)
            self.config(image=self.photo)
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {e}")
            self.config(image='', text='🖼️')

    def set_image(self, image: Optional[ImageTk.PhotoImage]):
        """Sets the label's image, falling back to a placeholder if None."""
        if image:
            self.photo = image
            self.config(image=self.photo, text='')
        else:
            self._create_placeholder()

# ==============================================================================
# WIDGET: ProgressDialog
# ==============================================================================
class ProgressDialog(tk.Toplevel):
    """A modal dialog to show progress for long-running, non-UI tasks."""
    def __init__(self, parent, title: str = "Working..."):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.message_var = tk.StringVar(value="Please wait...")
        self.progress_var = tk.DoubleVar(value=0)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        ttk.Label(main_frame, textvariable=self.message_var, wraplength=300).pack(pady=(0, 10))
        ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate", variable=self.progress_var).pack(pady=10)
        self.after(50, self._center_window)

    def _center_window(self):
        self.update_idletasks()
        parent_x, parent_y = self.parent.winfo_x(), self.parent.winfo_y()
        parent_w, parent_h = self.parent.winfo_width(), self.parent.winfo_height()
        dialog_w, dialog_h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        self.geometry(f"+{x}+{y}")

    def update_progress(self, value: float, message: str):
        self.progress_var.set(max(0, min(100, value)))
        self.message_var.set(message)
        self.update_idletasks()

    def close(self):
        self.grab_release()
        self.destroy()