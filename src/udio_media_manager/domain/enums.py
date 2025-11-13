"""
Enumerations for the Udio Media Manager domain. (DEFINITIVE, DE-DUPLICATED VERSION)
"""

from enum import Enum, auto
from typing import List, Set, Optional
from pathlib import Path

# --- File Type Extensions Mapping ---
# MOVED OUTSIDE the FileType class to prevent Enum metaclass conflicts. This is the definitive fix.
FILE_TYPE_EXTENSIONS = {
    'audio': {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'},
    'video': {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'},
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif', '.tiff', '.svg'},
    'metadata': {'.txt', '.json', '.xml', '.md'},
    'lyrics': {'.lrc', '.srt'},
    'art': {'.avif', '.jpg', '.jpeg', '.png', '.webp'},
    'thumbnail': {'.jpg', '.jpeg', '.png', '.webp', '.avif'},
    'waveform': {'.png', '.jpg', '.jpeg', '.svg'}
}

class SortKey(str, Enum):
    """Available sort keys for track listing."""
    TITLE = "title"
    ARTIST = "artist"
    DURATION = "duration"
    PLAYS = "plays"
    LIKES = "likes"
    DATE = "created_date"
    FILE_SIZE = "file_size"
    RATING = "rating"
    PLAY_COUNT = "play_count"
    LAST_PLAYED = "last_played_date"
    
    @property
    def display_name(self) -> str:
        name_map = {
            'TITLE': 'Title', 'ARTIST': 'Artist', 'DURATION': 'Duration',
            'PLAYS': 'Plays', 'LIKES': 'Likes', 'DATE': 'Date Created',
            'FILE_SIZE': 'File Size', 'RATING': 'Rating',
            'PLAY_COUNT': 'Play Count', 'LAST_PLAYED': 'Last Played'
        }
        return name_map.get(self.name, self.name.replace('_', ' ').title())

    @classmethod
    def from_string(cls, value: str) -> 'SortKey':
        if not value: raise ValueError("Sort key value cannot be empty")
        lookup = value.lower().strip()
        for member in cls:
            if member.value.lower() == lookup or member.name.lower() == lookup:
                return member
        raise ValueError(f"'{value}' is not a valid SortKey.")

    @classmethod
    def get_default(cls) -> 'SortKey': return cls.TITLE
    @classmethod
    def get_available_keys(cls) -> List['SortKey']: return list(cls)
    @classmethod
    def get_display_names(cls) -> List[str]: return [m.display_name for m in cls]


class TrackStatus(str, Enum):
    """Represents the publication or workflow status of a track."""
    DRAFT = "draft"
    FINISHED = "finished"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    PROCESSING = "processing"
    ERROR = "error"

    @property
    def display_name(self) -> str: return self.value.capitalize()
    @classmethod
    def from_string(cls, value: str) -> 'TrackStatus':
        if not value: return cls.DRAFT
        lookup = value.lower().strip()
        for member in cls:
            if member.value.lower() == lookup: return member
        return cls.DRAFT
    @classmethod
    def get_active_statuses(cls) -> List['TrackStatus']: return [cls.DRAFT, cls.FINISHED, cls.PUBLISHED, cls.PROCESSING]
    @classmethod
    def get_inactive_statuses(cls) -> List['TrackStatus']: return [cls.ARCHIVED, cls.ERROR]


class FileType(str, Enum):
    """Supported file types associated with Udio tracks."""
    AUDIO = "audio"
    VIDEO = "video"
    METADATA = "metadata"
    LYRICS = "lyrics"
    IMAGE = "image"
    THUMBNAIL = "thumbnail"
    ART = "art"
    WAVEFORM = "waveform"
    UNKNOWN = "unknown"
    
    @property
    def display_name(self) -> str: return self.value.capitalize()

    @classmethod
    def from_extension(cls, extension: str) -> 'FileType':
        """Gets the corresponding FileType from a file extension string."""
        if not extension: return cls.UNKNOWN
        ext_lower = ('.' + extension.lower().lstrip('.'))
        for file_type_value, extensions_set in FILE_TYPE_EXTENSIONS.items():
            if ext_lower in extensions_set:
                return cls(file_type_value)
        return cls.UNKNOWN

    @classmethod
    def from_filename(cls, filename: str) -> 'FileType':
        """Determines FileType from a filename."""
        if not filename: return cls.UNKNOWN
        return cls.from_extension(Path(filename).suffix)

    def get_extensions(self) -> Set[str]:
        """Returns all file extensions for this file type."""
        return FILE_TYPE_EXTENSIONS.get(self.value, set())
    
    @classmethod
    def get_supported_extensions(cls) -> Set[str]:
        """Returns all supported file extensions across all file types."""
        return {ext for ext_set in FILE_TYPE_EXTENSIONS.values() for ext in ext_set}
    
    @classmethod
    def is_supported_extension(cls, extension: str) -> bool:
        """Checks if a file extension is supported."""
        return cls.from_extension(extension) is not cls.UNKNOWN


class ScanStatus(Enum):
    """Represents the lifecycle status of a directory scanning operation."""
    PENDING, RUNNING, COMPLETED, CANCELLED, ERROR = auto(), auto(), auto(), auto(), auto()
    @property
    def display_name(self) -> str: return self.name.capitalize()
    @property
    def is_active(self) -> bool: return self in [self.PENDING, self.RUNNING]
    @property
    def is_final(self) -> bool: return self in [self.COMPLETED, self.CANCELLED, self.ERROR]

class ThemeMode(str, Enum):
    """Defines the available UI theme modes."""
    LIGHT, DARK, SYSTEM = "light", "dark", "system"
    @property
    def display_name(self) -> str: return self.value.capitalize()
    @classmethod
    def from_string(cls, value: str) -> 'ThemeMode':
        if not value: return cls.SYSTEM
        lookup = value.lower().strip()
        for member in cls:
            if member.value == lookup: return member
        return cls.SYSTEM
    @classmethod
    def get_default(cls) -> 'ThemeMode': return cls.SYSTEM

class PlaybackState(str, Enum):
    """Represents the current state of audio playback."""
    STOPPED, PLAYING, PAUSED, BUFFERING, ERROR = "stopped", "playing", "paused", "buffering", "error"
    @property
    def display_name(self) -> str: return self.value.capitalize()
    @property
    def is_playing(self) -> bool: return self == self.PLAYING
    @property
    def can_play(self) -> bool: return self in [self.STOPPED, self.PAUSED]
    @property
    def can_pause(self) -> bool: return self == self.PLAYING
    @property
    def can_stop(self) -> bool: return self in [self.PLAYING, self.PAUSED, self.BUFFERING]

class ExportFormat(str, Enum):
    """Supported export formats for track data."""
    JSON, CSV, XML, PLAIN_TEXT = "json", "csv", "xml", "txt"
    @property
    def display_name(self) -> str: return self.name
    @property
    def file_extension(self) -> str: return f".{self.value}"
    @classmethod
    def from_extension(cls, extension: str) -> Optional['ExportFormat']:
        ext = extension.lower().lstrip('.')
        for member in cls:
            if member.value == ext: return member
        return None

class SearchScope(str, Enum):
    """Defines the scope for search operations."""
    ALL, TITLE, ARTIST, TAGS, LYRICS, PROMPT = "all", "title", "artist", "tags", "lyrics", "prompt"
    @property
    def display_name(self) -> str: return self.value.capitalize()
    @classmethod
    def get_default(cls) -> 'SearchScope': return cls.ALL