# domain/__init__.py - Final Corrected Version

"""
This package defines the core business objects (domain models), data transfer
objects (DTOs), and enumerations for the Udio Media Manager application.
"""

from .dto import (
    ExportRequestDTO,
    ImportResultDTO,
    ScanProgressDTO,
    ScanRequestDTO,
    TrackQueryDTO,
    TrackUpdateDTO,
)
from .enums import FileType, ScanStatus, SortKey, ThemeMode, TrackStatus
from .models import ScanResult, Track

__all__ = [
    # DTOs
    "TrackUpdateDTO",
    "TrackQueryDTO",
    "ScanRequestDTO",
    "ScanProgressDTO",
    "ExportRequestDTO",
    "ImportResultDTO",
    # Enums
    "SortKey",
    "TrackStatus",
    "FileType",
    "ScanStatus",
    "ThemeMode",
    # Models
    "Track",
    "ScanResult",
]