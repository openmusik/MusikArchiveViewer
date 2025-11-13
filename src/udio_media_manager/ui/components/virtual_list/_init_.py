"""
Virtual List Component
=====================

A high-performance virtual list implementation for handling large datasets
efficiently in Tkinter applications.
"""

# Import the main classes to make them available at package level
from .core import VirtualList
from .base import VirtualListItem

# Explicitly define what should be available when importing from this package
__all__ = ['VirtualList', 'VirtualListItem']