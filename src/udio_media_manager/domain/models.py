# models.py - Fully Upgraded with Artwork Path Support

"""
Core domain models for the Udio Media Manager.

These dataclasses represent the fundamental entities of the application,
such as a Track and the result of a Scan operation.

UPGRADE: Now includes artwork_file_path field for persistent artwork storage.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enums import FileType, ScanStatus, TrackStatus


@dataclass
class Track:
    """
    Represents a single Udio track, encapsulating ALL metadata fields.
    """
    # === REQUIRED FIELDS ===
    song_id: str
    file_path: Path

    # === CORE TRACK INFO ===
    title: str = "Untitled"
    artist: str = "Unknown"
    duration: float = 0.0
    created_date: Optional[datetime] = None
    
    # === IDENTIFIERS ===
    generation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # === URLS AND MEDIA ===
    source_url: Optional[str] = None
    audio_url: Optional[str] = None
    album_art_url: Optional[str] = None
    video_url: Optional[str] = None
    artist_image_url: Optional[str] = None
    
    # === CONTENT AND METADATA ===
    prompt: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    user_tags: List[str] = field(default_factory=list)
    lyrics: Optional[str] = None
    audio_conditioning_type: Optional[str] = None
    capture_method: Optional[str] = None
    
    # === RELATIONSHIP INFO ===
    parent_id: Optional[str] = None
    original_song_path: Optional[str] = None
    relationship_type: Optional[str] = None
    relationship_info: Dict[str, Any] = field(default_factory=dict)
    
    # === COLLABORATION INFO ===
    collaboration_info: Dict[str, Any] = field(default_factory=dict)
    attribution: Optional[str] = None
    
    # === STATUS AND ENGAGEMENT ===
    status: TrackStatus = TrackStatus.DRAFT
    plays: int = 0
    likes: int = 0
    is_finished: bool = False
    is_publishable: bool = False
    is_disliked: bool = False
    is_liked: bool = False
    is_favorite: bool = False
    
    # === FILE SYSTEM INFO ===
    file_size: int = 0
    file_size_mb: float = 0.0
    file_location: Optional[str] = None
    file_absolute_path: Optional[str] = None
    files: Dict[FileType, Path] = field(default_factory=dict)
    playlist_context: Optional[str] = None
    artwork_file_path: Optional[str] = None  # NEW: Persistent artwork path
    
    # === EXPORT INFO ===
    exported_date: Optional[datetime] = None
    export_tool: Optional[str] = None
    
    # === EXTENDED METADATA ===
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    audio_metadata: Dict[str, Any] = field(default_factory=dict)
    export_info: Dict[str, Any] = field(default_factory=dict)
    lyrics_data: Dict[str, Any] = field(default_factory=dict)
    user_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensures data is normalized after the object is created."""
        # Convert string paths to Path objects
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
        
        # Convert artwork_file_path to Path if it's a string
        if isinstance(self.artwork_file_path, str) and self.artwork_file_path:
            try:
                # Don't convert empty strings
                if self.artwork_file_path.strip():
                    # Keep as string for database compatibility, conversion happens in property
                    pass
            except Exception:
                self.artwork_file_path = None
            
        # Convert string lists to actual lists
        if isinstance(self.tags, str):
            self.tags = json.loads(self.tags) if self.tags else []
        if isinstance(self.user_tags, str):
            self.user_tags = json.loads(self.user_tags) if self.user_tags else []
            
        # Convert string dicts to actual dicts
        string_fields = [
            'custom_fields', 'collaboration_info', 'audio_metadata', 
            'export_info', 'lyrics_data', 'user_data', 'relationship_info'
        ]
        for field_name in string_fields:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, json.loads(value) if value else {})
        
        # Ensure status is a TrackStatus enum
        if isinstance(self.status, str):
            try:
                self.status = TrackStatus.from_string(self.status)
            except (ValueError, AttributeError):
                self.status = TrackStatus.DRAFT

    @property
    def has_audio(self) -> bool:
        """Checks if an audio file is associated with the track."""
        return self.audio_path is not None
    
    @property
    def audio_path(self) -> Optional[Path]:
        """
        Get the audio file path with multiple fallback strategies.
        
        Priority:
        1. files dictionary (for newly scanned tracks)
        2. file_path if it's an audio file
        3. file_absolute_path if available
        4. Reconstruct from file_path by looking for audio file
        """
        # Strategy 1: Check files dictionary
        if hasattr(self, 'files') and FileType.AUDIO in self.files:
            return self.files[FileType.AUDIO]
        
        # Strategy 2: Check if file_path itself is an audio file
        if self.file_path:
            try:
                file_path_obj = Path(self.file_path) if isinstance(self.file_path, str) else self.file_path
                
                # Check if it's an audio file
                audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
                if file_path_obj.suffix.lower() in audio_extensions and file_path_obj.exists():
                    return file_path_obj
                    
                # If file_path is metadata/text, look for audio file with same base name
                if file_path_obj.exists():
                    parent = file_path_obj.parent
                    base_name = file_path_obj.stem
                    
                    # Try to find audio file with same name
                    for ext in audio_extensions:
                        audio_file = parent / f"{base_name}{ext}"
                        if audio_file.exists():
                            return audio_file
                            
            except Exception as e:
                print(f"Error checking file_path for audio: {e}")
        
        # Strategy 3: Check file_absolute_path
        if hasattr(self, 'file_absolute_path') and self.file_absolute_path:
            try:
                abs_path = Path(self.file_absolute_path) if isinstance(self.file_absolute_path, str) else self.file_absolute_path
                if abs_path.exists():
                    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
                    if abs_path.suffix.lower() in audio_extensions:
                        return abs_path
            except Exception:
                pass
        
        # Strategy 4: Check custom_fields for audio URLs
        if hasattr(self, 'custom_fields') and self.custom_fields:
            for field in ['audio_url', 'source_url', 'audio_path']:
                if field in self.custom_fields and self.custom_fields[field]:
                    try:
                        potential_path = Path(self.custom_fields[field])
                        if potential_path.exists():
                            return potential_path
                    except Exception:
                        pass
        
        return None

    @property
    def audio_path(self) -> Optional[Path]:
        """
        Get the audio file path with multiple fallback strategies.
        
        Priority:
        1. files dictionary (for newly scanned tracks)
        2. file_path if it's an audio file
        3. file_absolute_path if available
        4. Reconstruct from file_path by looking for audio file
        """
        # Strategy 1: Check files dictionary
        if hasattr(self, 'files') and FileType.AUDIO in self.files:
            return self.files[FileType.AUDIO]
        
        # Strategy 2: Check if file_path itself is an audio file
        if self.file_path:
            try:
                file_path_obj = Path(self.file_path) if isinstance(self.file_path, str) else self.file_path
                
                # Check if it's an audio file
                audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
                if file_path_obj.suffix.lower() in audio_extensions and file_path_obj.exists():
                    return file_path_obj
                    
                # If file_path is metadata/text, look for audio file with same base name
                if file_path_obj.exists():
                    parent = file_path_obj.parent
                    base_name = file_path_obj.stem
                    
                    # Try to find audio file with same name
                    for ext in audio_extensions:
                        audio_file = parent / f"{base_name}{ext}"
                        if audio_file.exists():
                            return audio_file
                            
            except Exception as e:
                # Don't import logger here, just pass silently
                pass
        
        # Strategy 3: Check file_absolute_path
        if hasattr(self, 'file_absolute_path') and self.file_absolute_path:
            try:
                abs_path = Path(self.file_absolute_path) if isinstance(self.file_absolute_path, str) else self.file_absolute_path
                if abs_path.exists():
                    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
                    if abs_path.suffix.lower() in audio_extensions:
                        return abs_path
            except Exception:
                pass
        
        # Strategy 4: Check custom_fields for audio URLs
        if hasattr(self, 'custom_fields') and self.custom_fields:
            for field in ['audio_url', 'source_url', 'audio_path']:
                if field in self.custom_fields and self.custom_fields[field]:
                    try:
                        potential_path = Path(self.custom_fields[field])
                        if potential_path.exists():
                            return potential_path
                    except Exception:
                        pass
        
        return None

    @property
    def has_art(self) -> bool:
        """Checks if art is available for this track."""
        # Check persistent artwork_file_path first (DATABASE)
        if self.artwork_file_path:
            try:
                if isinstance(self.artwork_file_path, str):
                    artwork_path = Path(self.artwork_file_path)
                else:
                    artwork_path = self.artwork_file_path
                    
                if artwork_path.exists():
                    return True
            except Exception:
                pass
        
        # Fallback to files dictionary (IN-MEMORY during scan)
        image_types = [FileType.IMAGE, FileType.THUMBNAIL, FileType.ART]
        return any(ft in self.files for ft in image_types)

    @property
    def art_path(self) -> Optional[Path]:
        """Get the best available art path with fallbacks."""
        # Priority 1: artwork_file_path from database (convert string to Path)
        if self.artwork_file_path:
            try:
                # Ensure it's a Path object
                if isinstance(self.artwork_file_path, str):
                    artwork_path = Path(self.artwork_file_path)
                else:
                    artwork_path = self.artwork_file_path
                    
                if artwork_path.exists():
                    return artwork_path
            except Exception:
                pass  # Invalid path, continue to fallbacks
        
        # Priority 2: files dictionary (for newly scanned tracks)
        image_types = [FileType.IMAGE, FileType.THUMBNAIL, FileType.ART]
        for file_type in image_types:
            if file_type in self.files:
                return self.files[file_type]
        
        # Priority 3: Look for sidecar artwork files
        if self.file_path:
            try:
                if isinstance(self.file_path, str):
                    file_path_obj = Path(self.file_path)
                else:
                    file_path_obj = self.file_path
                    
                if file_path_obj.exists():
                    artwork_patterns = [
                        f"{file_path_obj.stem} - Artwork.avif",
                        f"{file_path_obj.stem} - Artwork.jpg",
                        f"{file_path_obj.stem} - Artwork.jpeg",
                        f"{file_path_obj.stem} - Artwork.png",
                    ]
                    for pattern in artwork_patterns:
                        artwork_path = file_path_obj.parent / pattern
                        if artwork_path.exists():
                            return artwork_path
            except Exception:
                pass  # Invalid path
        
        return None

    @property
    def avif_path(self) -> Optional[Path]:
        """Get AVIF art path specifically."""
        # Check artwork_file_path first (convert string to Path)
        if self.artwork_file_path:
            try:
                if isinstance(self.artwork_file_path, str):
                    artwork_path = Path(self.artwork_file_path)
                else:
                    artwork_path = self.artwork_file_path
                    
                if artwork_path.exists() and artwork_path.suffix.lower() == '.avif':
                    return artwork_path
            except Exception:
                pass
        
        # Check files dictionary
        if FileType.ART in self.files:
            return self.files[FileType.ART]
        
        # Look for sidecar AVIF
        if self.file_path:
            try:
                if isinstance(self.file_path, str):
                    file_path_obj = Path(self.file_path)
                else:
                    file_path_obj = self.file_path
                    
                if file_path_obj.exists():
                    avif_path = file_path_obj.parent / f"{file_path_obj.stem} - Artwork.avif"
                    if avif_path.exists():
                        return avif_path
            except Exception:
                pass
        
        return None

    @property
    def duration_formatted(self) -> str:
        """Returns the duration in a user-friendly MM:SS format."""
        if not self.duration or self.duration <= 0:
            return "--:--"
        minutes, seconds = divmod(int(self.duration), 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def has_video(self) -> bool:
        """Checks if this track has an associated video."""
        return bool(self.video_url and self.video_url.strip())
    
    @property
    def has_lyrics(self) -> bool:
        """Checks if this track has lyrics."""
        return bool(self.lyrics and self.lyrics.strip())
    
    @property
    def collaborators(self) -> List[str]:
        """Extracts collaborator names from collaboration info."""
        return self.collaboration_info.get('collaborators', [])
    
    @property
    def lyrics_line_count(self) -> int:
        """Gets the number of lines in the lyrics."""
        if not self.lyrics:
            return 0
        return len(self.lyrics.split('\n'))

    # Database field mapping - NOW INCLUDES artwork_file_path
    _DB_FIELDS: Tuple[str, ...] = (
        # Core identifiers
        'song_id', 'generation_id', 'user_id',
        
        # Basic track info
        'title', 'artist', 'duration', 'created_date',
        
        # URLs and media
        'source_url', 'audio_url', 'album_art_url', 'video_url', 'artist_image_url',
        
        # Content and metadata
        'prompt', 'description', 'tags', 'user_tags', 'lyrics', 
        'audio_conditioning_type', 'capture_method',
        
        # Relationship info
        'parent_id', 'original_song_path', 'relationship_type', 'relationship_info',
        
        # Collaboration info
        'collaboration_info', 'attribution',
        
        # Status and engagement
        'plays', 'likes', 'is_finished', 'is_publishable', 'is_disliked', 
        'is_liked', 'is_favorite', 'status',
        
        # File system info
        'file_path', 'file_size', 'file_size_mb', 'file_location', 
        'file_absolute_path', 'playlist_context', 'artwork_file_path',  # NEW
        
        # Export info
        'exported_date', 'export_tool',
        
        # Extended metadata
        'custom_fields', 'audio_metadata', 'export_info', 'lyrics_data', 'user_data'
    )

    def to_row(self) -> Tuple:
        """Serializes the Track object into a tuple suitable for a database row."""
        status_value = self.status.value if hasattr(self.status, 'value') else str(self.status)
        
        # Convert complex fields to JSON
        tags_json = json.dumps(self.tags)
        user_tags_json = json.dumps(self.user_tags)
        relationship_info_json = json.dumps(self._make_serializable(self.relationship_info))
        collaboration_info_json = json.dumps(self._make_serializable(self.collaboration_info))
        custom_fields_json = json.dumps(self._make_serializable(self.custom_fields))
        audio_metadata_json = json.dumps(self._make_serializable(self.audio_metadata))
        export_info_json = json.dumps(self._make_serializable(self.export_info))
        lyrics_data_json = json.dumps(self._make_serializable(self.lyrics_data))
        user_data_json = json.dumps(self._make_serializable(self.user_data))
        
        return (
            # Core identifiers
            self.song_id, self.generation_id, self.user_id,
            
            # Basic track info
            self.title, self.artist, self.duration, self.created_date,
            
            # URLs and media
            self.source_url, self.audio_url, self.album_art_url, 
            self.video_url, self.artist_image_url,
            
            # Content and metadata
            self.prompt, self.description, tags_json, user_tags_json, self.lyrics,
            self.audio_conditioning_type, self.capture_method,
            
            # Relationship info
            self.parent_id, self.original_song_path, self.relationship_type,
            relationship_info_json,
            
            # Collaboration info
            collaboration_info_json, self.attribution,
            
            # Status and engagement
            self.plays, self.likes, self.is_finished, self.is_publishable,
            self.is_disliked, self.is_liked, self.is_favorite, status_value,
            
            # File system info - NOW INCLUDES artwork_file_path
            str(self.file_path), self.file_size, self.file_size_mb,
            self.file_location, self.file_absolute_path, self.playlist_context,
            self.artwork_file_path,  # NEW
            
            # Export info
            self.exported_date, self.export_tool,
            
            # Extended metadata
            custom_fields_json, audio_metadata_json, export_info_json,
            lyrics_data_json, user_data_json
        )

    def _make_serializable(self, data: Any) -> Any:
        """Convert data to a JSON-serializable format."""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, (list, tuple)):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Path):
            return str(data)
        elif hasattr(data, '__dict__'):
            try:
                return self._make_serializable(data.__dict__)
            except:
                return str(data)
        else:
            try:
                json.dumps(data)
                return data
            except (TypeError, ValueError):
                return str(data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Track':
        """Deserializes a database row into a Track object."""
        data = {}
        for key in cls._DB_FIELDS:
            if key in row.keys():
                data[key] = row[key]
            else:
                if key in ['song_id', 'file_path']:
                    raise ValueError(f"Database row is missing required field '{key}'")
                data[key] = None
        
        # Convert file_path
        data['file_path'] = Path(data['file_path'])
        
        # Handle status conversion
        if 'status' in data:
            try:
                data['status'] = TrackStatus.from_string(data['status'])
            except (ValueError, AttributeError):
                data['status'] = TrackStatus.DRAFT
        
        # Handle datetime fields
        datetime_fields = ['created_date', 'exported_date']
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    data[field_name] = None
        
        # Deserialize JSON fields
        json_fields = [
            'tags', 'user_tags', 'collaboration_info', 'custom_fields',
            'audio_metadata', 'export_info', 'lyrics_data', 'user_data', 'relationship_info'
        ]
        for field_name in json_fields:
            if field_name in data and data[field_name]:
                if isinstance(data[field_name], str):
                    try:
                        data[field_name] = json.loads(data[field_name])
                    except json.JSONDecodeError:
                        data[field_name] = [] if field_name in ['tags', 'user_tags'] else {}
                elif data[field_name] is None:
                    data[field_name] = [] if field_name in ['tags', 'user_tags'] else {}
            else:
                data[field_name] = [] if field_name in ['tags', 'user_tags'] else {}
        
        # Convert boolean fields
        boolean_fields = [
            'is_finished', 'is_publishable', 'is_disliked', 'is_liked', 'is_favorite'
        ]
        for field_name in boolean_fields:
            if field_name in data:
                if isinstance(data[field_name], str):
                    data[field_name] = data[field_name].lower() in ['true', '1', 'yes']
                elif data[field_name] is None:
                    data[field_name] = False
        
        # Convert numeric fields
        numeric_fields = ['plays', 'likes', 'file_size', 'duration']
        for field_name in numeric_fields:
            if field_name in data and data[field_name] is not None:
                try:
                    data[field_name] = float(data[field_name]) if field_name == 'duration' else int(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = 0
        
        return cls(**data)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update track fields from a dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                if key == 'status' and isinstance(value, str):
                    try:
                        setattr(self, key, TrackStatus.from_string(value))
                    except (ValueError, AttributeError):
                        setattr(self, key, TrackStatus.DRAFT)
                elif key == 'file_path' and isinstance(value, (str, Path)):
                    setattr(self, key, Path(value))
                else:
                    setattr(self, key, value)

    def update_from_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update track fields from a metadata parser result dictionary."""
        field_mapping = {
            'title': 'title',
            'artist': 'artist',
            'duration': 'duration',
            'created_date': 'created_date',
            'song_id': 'song_id',
            'generation_id': 'generation_id',
            'user_id': 'user_id',
            'source_url': 'source_url',
            'audio_url': 'audio_url',
            'album_art_url': 'album_art_url',
            'video_url': 'video_url',
            'artist_image_url': 'artist_image_url',
            'prompt': 'prompt',
            'tags': 'tags',
            'user_tags': 'user_tags',
            'lyrics': 'lyrics',
            'audio_conditioning_type': 'audio_conditioning_type',
            'capture_method': 'capture_method',
            'collaboration_info': 'collaboration_info',
            'attribution': 'attribution',
            'plays': 'plays',
            'likes': 'likes',
            'finished': 'is_finished',
            'publishable': 'is_publishable',
            'disliked': 'is_disliked',
            'liked': 'is_liked',
            'file_size': 'file_size',
            'exported_date': 'exported_date',
            'export_tool': 'export_tool',
            'custom_fields': 'custom_fields',
            'audio_metadata': 'audio_metadata',
            'export_info': 'export_info',
            'lyrics_data': 'lyrics_data',
            'user_data': 'user_data'
        }
        
        for metadata_key, model_key in field_mapping.items():
            if metadata_key in metadata and metadata[metadata_key] is not None:
                setattr(self, model_key, metadata[metadata_key])

    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary for serialization or API responses."""
        result = {}
        for field_name in self._DB_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Path):
                value = str(value)
            elif isinstance(value, TrackStatus):
                value = value.value
            result[field_name] = value
        return result

    def __str__(self) -> str:
        """String representation of the track."""
        return f"Track('{self.title}' by {self.artist} - {self.duration_formatted})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"Track(song_id='{self.song_id}', title='{self.title}', "
                f"artist='{self.artist}', duration={self.duration}, "
                f"status={self.status})")


@dataclass
class ScanResult:
    """Holds the final summary and status of a directory scan operation."""
    scan_path: Path
    status: ScanStatus = ScanStatus.PENDING
    processed_files: int = 0
    failed_files: int = 0
    error_message: Optional[str] = None
    errors: Dict[str, str] = field(default_factory=dict)

    def add_error(self, file_path: str, message: str):
        """Adds a specific file processing error to the results."""
        self.errors[file_path] = message

    @property
    def total_files(self) -> int:
        """Returns the total number of files processed."""
        return self.processed_files + self.failed_files

    @property
    def success_rate(self) -> float:
        """Returns the success rate as a percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100