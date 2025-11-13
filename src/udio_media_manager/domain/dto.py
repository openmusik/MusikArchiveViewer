# dto.py - Fully Upgraded & Bug Fixed

"""
Data Transfer Objects (DTOs) for API and inter-service communication.

DTOs are simple, immutable data classes used to pass structured data between
different layers of the application (e.g., from the UI to a service, or from a
service to the database layer) without exposing internal domain models.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .enums import SortKey


@dataclass(frozen=True)
class TrackUpdateDTO:
    """DTO for carrying track metadata updates."""
    song_id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the DTO to a dictionary, excluding fields that are None."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class TrackQueryDTO:
    """
    DTO for specifying complex filters and sorting options when querying tracks.
    An empty instance with default values will fetch all tracks sorted by plays.
    """
    search_text: Optional[str] = None
    artist_filter: Optional[str] = None
    status_filter: Optional[str] = None  # Changed from TrackStatus to string to avoid circular import
    tags_filter: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    min_plays: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: SortKey = SortKey.PLAYS
    sort_descending: bool = True
    limit: Optional[int] = None
    offset: Optional[int] = None
    
    def is_empty(self) -> bool:
        """Checks if the query has any specific filters applied."""
        # Note: sort_by and sort_descending are not considered filters.
        return all(
            getattr(self, field) is None 
            for field in ['search_text', 'artist_filter', 'status_filter', 
                         'tags_filter', 'min_duration', 'max_duration',
                         'min_plays', 'date_from', 'date_to', 'is_favorite']
        )


@dataclass(frozen=True)
class ScanRequestDTO:
    """DTO for initiating a directory scan with specific parameters."""
    scan_path: Path
    recursive: bool = True
    force_rescan: bool = False  # If true, re-process all files, not just new ones.


@dataclass(frozen=True)
class ScanProgressDTO:
    """
    DTO for reporting scan progress from the background thread to the UI.
    Contains a simple percentage and a descriptive message.
    """
    progress: float
    message: str


@dataclass(frozen=True)
class ExportRequestDTO:
    """DTO for specifying options for exporting track data."""
    output_format: str  # e.g., 'json', 'csv'
    output_path: Path
    track_ids: Optional[List[str]] = None  # If None, export all tracks
    include_lyrics: bool = False


@dataclass(frozen=True)
class ImportResultDTO:
    """DTO for summarizing the result of an import operation."""
    total_processed: int
    successful_imports: int
    failed_imports: int
    errors: List[str]