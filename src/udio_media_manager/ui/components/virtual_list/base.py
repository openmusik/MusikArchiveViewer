"""
Base class for virtual list items
"""

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Optional

class VirtualListItem(ABC):
    """
    Enhanced abstract base class for items that can be displayed in the VirtualList.
    """
    
    @abstractmethod
    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create and return the widget for this list item."""
        raise NotImplementedError

    @abstractmethod
    def update_widget(self, widget: tk.Widget, is_selected: bool) -> None:
        """Update the widget's content and state (e.g., selection)."""
        raise NotImplementedError

    @abstractmethod
    def get_height(self) -> int:
        """Return the item's height in pixels."""
        raise NotImplementedError

    def destroy_widget(self, widget: tk.Widget) -> None:
        """Optional: Clean up widget resources when no longer needed."""
        pass