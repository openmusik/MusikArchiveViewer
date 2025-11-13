"""
Data validation utilities for Udio Media Manager.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from ..core.exceptions import TrackValidationError
from ..domain.models import Track
from ..domain.enums import FileType
from ..utils.logging import get_logger


logger = get_logger(__name__)


class TrackValidator:
    """
    Validator for Track objects and related data.
    """
    
    # UUID pattern for validation
    UUID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
    
    @staticmethod
    def validate_track(track: Track) -> List[str]:
        """
        Validate a Track object for completeness and data integrity.
        
        Args:
            track: Track object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate required fields
        if not track.song_id:
            errors.append("Song ID is required")
        elif not TrackValidator.is_valid_uuid(track.song_id):
            errors.append(f"Invalid Song ID format: {track.song_id}")
            
        if not track.base_name:
            errors.append("Base name is required")
            
        if not track.txt or not Path(track.txt).exists():
            errors.append("Metadata file (.txt) is required and must exist")
            
        # Validate file paths
        for file_type in [FileType.MP3, FileType.MP4, FileType.AVIF, FileType.LRC]:
            path_attr = file_type.value
            path_value = getattr(track, path_attr)
            
            if path_value and not Path(path_value).exists():
                errors.append(f"{file_type.value.upper()} file does not exist: {path_value}")
                
        # Validate metadata fields
        if not track.title or track.title.strip() == "Untitled":
            errors.append("Title is required and cannot be 'Untitled'")
            
        if not track.artist or track.artist.strip() == "Unknown":
            errors.append("Artist is required and cannot be 'Unknown'")
            
        # Validate numeric fields
        if track.duration < 0:
            errors.append("Duration cannot be negative")
            
        if track.plays < 0:
            errors.append("Plays cannot be negative")
            
        if track.likes < 0:
            errors.append("Likes cannot be negative")
            
        if track.file_size < 0:
            errors.append("File size cannot be negative")
            
        # Validate date fields
        if track.created:
            try:
                if track.created > datetime.now():
                    errors.append("Creation date cannot be in the future")
            except (TypeError, ValueError):
                errors.append("Invalid creation date format")
                
        # Validate tags
        if track.tags:
            for tag in track.tags:
                if not isinstance(tag, str) or not tag.strip():
                    errors.append("Tags must be non-empty strings")
                    
        # Validate lyrics structure
        if track.lyrics:
            for timestamp, line in track.lyrics:
                if not isinstance(timestamp, (int, float)) or timestamp < 0:
                    errors.append("Lyric timestamps must be non-negative numbers")
                if not isinstance(line, str):
                    errors.append("Lyric lines must be strings")
                    
        return errors
        
    @staticmethod
    def is_valid_uuid(uuid_string: str) -> bool:
        """
        Check if string is a valid UUID.
        
        Args:
            uuid_string: String to validate
            
        Returns:
            True if valid UUID format
        """
        try:
            UUID(uuid_string)
            return True
        except (ValueError, AttributeError):
            return False
            
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> List[str]:
        """
        Validate metadata dictionary.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = ['title', 'artist']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Required field missing: {field}")
                
        # Validate field types
        type_checks = [
            ('title', str),
            ('artist', str),
            ('duration', (int, float)),
            ('plays', int),
            ('likes', int),
            ('finished', bool),
            ('publishable', bool),
            ('disliked', bool),
        ]
        
        for field, expected_type in type_checks:
            if field in metadata and metadata[field] is not None:
                if not isinstance(metadata[field], expected_type):
                    errors.append(f"Field '{field}' has invalid type: {type(metadata[field])}")
                    
        # Validate date field if present
        if 'created' in metadata and metadata['created']:
            if not isinstance(metadata['created'], datetime):
                errors.append("Field 'created' must be a datetime object")
                
        # Validate tags if present
        if 'tags' in metadata and metadata['tags']:
            if not isinstance(metadata['tags'], list):
                errors.append("Field 'tags' must be a list")
            else:
                for tag in metadata['tags']:
                    if not isinstance(tag, str):
                        errors.append("All tags must be strings")
                        
        return errors


class FileValidator:
    """
    Validator for file-related operations.
    """
    
    @staticmethod
    def validate_file_path(file_path: Path, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate a file path.
        
        Args:
            file_path: Path to validate
            must_exist: Whether the file must exist
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not file_path:
                return False, "Path cannot be empty"
                
            if must_exist and not file_path.exists():
                return False, f"File does not exist: {file_path}"
                
            if must_exist and not file_path.is_file():
                return False, f"Path is not a file: {file_path}"
                
            # Check file size (basic sanity check)
            if must_exist:
                file_size = file_path.stat().st_size
                if file_size == 0:
                    return False, f"File is empty: {file_path}"
                if file_size > 100 * 1024 * 1024:  # 100MB
                    return False, f"File too large: {file_size / (1024*1024):.1f}MB"
                    
            return True, None
            
        except (OSError, PermissionError) as e:
            return False, f"File access error: {e}"
            
    @staticmethod
    def validate_directory_path(directory_path: Path, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate a directory path.
        
        Args:
            directory_path: Path to validate
            must_exist: Whether the directory must exist
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not directory_path:
                return False, "Path cannot be empty"
                
            if must_exist and not directory_path.exists():
                return False, f"Directory does not exist: {directory_path}"
                
            if must_exist and not directory_path.is_dir():
                return False, f"Path is not a directory: {directory_path}"
                
            # Test basic read access
            if must_exist:
                try:
                    next(directory_path.iterdir(), None)
                except PermissionError:
                    return False, f"No read permission for directory: {directory_path}"
                    
            return True, None
            
        except (OSError, PermissionError) as e:
            return False, f"Directory access error: {e}"


class DataSanitizer:
    """
    Utilities for sanitizing and normalizing data.
    """
    
    @staticmethod
    def sanitize_string(value: Any, default: str = "") -> str:
        """
        Sanitize a string value.
        
        Args:
            value: Value to sanitize
            default: Default value if sanitization fails
            
        Returns:
            Sanitized string
        """
        if value is None:
            return default
            
        try:
            sanitized = str(value).strip()
            return sanitized if sanitized else default
        except (ValueError, TypeError):
            return default
            
    @staticmethod
    def sanitize_integer(value: Any, default: int = 0) -> int:
        """
        Sanitize an integer value.
        
        Args:
            value: Value to sanitize
            default: Default value if sanitization fails
            
        Returns:
            Sanitized integer
        """
        if value is None:
            return default
            
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                # Extract numbers from string
                numbers = re.findall(r'\d+', value)
                return int(numbers[0]) if numbers else default
            else:
                return default
        except (ValueError, TypeError):
            return default
            
    @staticmethod
    def sanitize_float(value: Any, default: float = 0.0) -> float:
        """
        Sanitize a float value.
        
        Args:
            value: Value to sanitize
            default: Default value if sanitization fails
            
        Returns:
            Sanitized float
        """
        if value is None:
            return default
            
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # Extract numbers from string
                numbers = re.findall(r'\d+\.?\d*', value)
                return float(numbers[0]) if numbers else default
            else:
                return default
        except (ValueError, TypeError):
            return default
            
    @staticmethod
    def sanitize_boolean(value: Any, default: bool = False) -> bool:
        """
        Sanitize a boolean value.
        
        Args:
            value: Value to sanitize
            default: Default value if sanitization fails
            
        Returns:
            Sanitized boolean
        """
        if value is None:
            return default
            
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return bool(value)
        elif isinstance(value, str):
            true_values = ['true', 'yes', '1', 'on', 'finished', 'publishable']
            false_values = ['false', 'no', '0', 'off', 'disliked']
            
            value_lower = value.lower().strip()
            if value_lower in true_values:
                return True
            elif value_lower in false_values:
                return False
            else:
                return default
        else:
            return default
            
    @staticmethod
    def sanitize_tags(tags: Any) -> List[str]:
        """
        Sanitize tags list.
        
        Args:
            tags: Tags to sanitize
            
        Returns:
            Sanitized list of tags
        """
        if not tags:
            return []
            
        try:
            if isinstance(tags, str):
                # Try to parse as JSON first
                try:
                    import json
                    parsed = json.loads(tags)
                    if isinstance(parsed, list):
                        tags = parsed
                    else:
                        # Split by commas
                        tags = [tag.strip() for tag in tags.split(',')]
                except (json.JSONDecodeError, TypeError):
                    # Split by commas
                    tags = [tag.strip() for tag in tags.split(',')]
                    
            if isinstance(tags, list):
                sanitized = []
                for tag in tags:
                    if tag and isinstance(tag, str):
                        sanitized_tag = tag.strip()
                        if sanitized_tag:
                            sanitized.append(sanitized_tag)
                return sanitized
            else:
                return []
                
        except (ValueError, TypeError, AttributeError):
            return []
            
    @staticmethod
    def normalize_filename(filename: str) -> str:
        """
        Normalize filename by removing invalid characters.
        
        Args:
            filename: Filename to normalize
            
        Returns:
            Normalized filename
        """
        import re
        import os
        
        # Remove invalid characters for most file systems
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        normalized = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        normalized = normalized.strip('. ')
        
        # Ensure filename is not empty
        if not normalized:
            normalized = "unnamed_file"
            
        # Limit length (255 chars is typical max for most filesystems)
        if len(normalized) > 255:
            name, ext = os.path.splitext(normalized)
            normalized = name[:255 - len(ext)] + ext
            
        return normalized


class ValidationResult:
    """
    Container for validation results with detailed error information.
    """
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def add_error(self, error: str):
        """Add a validation error."""
        self.is_valid = False
        self.errors.append(error)
        
    def add_warning(self, warning: str):
        """Add a validation warning."""
        self.warnings.append(warning)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'has_errors': bool(self.errors),
            'has_warnings': bool(self.warnings),
        }
        
    def __bool__(self):
        return self.is_valid