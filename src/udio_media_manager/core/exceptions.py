"""
Custom exceptions for the Udio Media Manager.
"""

from pathlib import Path
from typing import Optional


class UdioManagerError(Exception):
    """Base exception for all Udio Media Manager errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(UdioManagerError):
    """Raised when there are issues with application configuration."""
    pass


class DatabaseError(UdioManagerError):
    """Raised for database-related errors."""
    
    def __init__(self, message: str, sql: Optional[str] = None, params: Optional[tuple] = None):
        self.sql = sql
        self.params = params
        super().__init__(message)


class FileSystemError(UdioManagerError):
    """Raised for file system operation errors."""
    
    def __init__(self, message: str, path: Optional[Path] = None, operation: Optional[str] = None):
        self.path = path
        self.operation = operation
        super().__init__(message)


class ScanError(UdioManagerError):
    """Raised during directory scanning operations."""
    
    def __init__(self, message: str, scan_path: Optional[Path] = None, phase: Optional[str] = None):
        self.scan_path = scan_path
        self.phase = phase
        super().__init__(message)


class MetadataParseError(UdioManagerError):
    """Raised when metadata parsing fails."""
    
    def __init__(self, message: str, file_path: Optional[Path] = None, content: Optional[str] = None):
        self.file_path = file_path
        self.content = content
        super().__init__(message)


class TrackValidationError(UdioManagerError):
    """Raised when track data validation fails."""
    
    def __init__(self, message: str, track_id: Optional[str] = None, field: Optional[str] = None):
        self.track_id = track_id
        self.field = field
        super().__init__(message)


class AudioPlaybackError(UdioManagerError):
    """Raised when audio playback fails."""
    
    def __init__(self, message: str, file_path: Optional[Path] = None, player: Optional[str] = None):
        self.file_path = file_path
        self.player = player
        super().__init__(message)


class ImageProcessingError(UdioManagerError):
    """Raised when image processing fails."""
    
    def __init__(self, message: str, image_path: Optional[Path] = None, operation: Optional[str] = None):
        self.image_path = image_path
        self.operation = operation
        super().__init__(message)


class ExportError(UdioManagerError):
    """Raised when data export fails."""
    
    def __init__(self, message: str, format: Optional[str] = None, output_path: Optional[Path] = None):
        self.format = format
        self.output_path = output_path
        super().__init__(message)


class DependencyError(UdioManagerError):
    """Raised when required dependencies are missing."""
    
    def __init__(self, message: str, dependency: Optional[str] = None, install_command: Optional[str] = None):
        self.dependency = dependency
        self.install_command = install_command
        super().__init__(message)


class CancellationError(UdioManagerError):
    """Raised when an operation is cancelled by the user."""
    pass


class ResourceCleanupError(UdioManagerError):
    """Raised when resource cleanup fails during shutdown."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        self.resource_type = resource_type
        super().__init__(message)