"""
Core infrastructure and application foundation.
"""

from .constants import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION,
    SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB, UUID_PATTERN,
    DATABASE_NAME, DATABASE_TIMEOUT, BATCH_INSERT_SIZE,
    DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, THUMBNAIL_SIZE, LIST_ITEM_HEIGHT,
    MAX_WORKER_THREADS, IMAGE_CACHE_SIZE, SCAN_BATCH_SIZE,
    THEME_COLORS, FONTS, get_default_scan_directories
)
from .exceptions import (
    UdioManagerError, ConfigurationError, DatabaseError, FileSystemError,
    ScanError, MetadataParseError, TrackValidationError, AudioPlaybackError,
    ImageProcessingError, ExportError, DependencyError, CancellationError,
    ResourceCleanupError
)
from .singleton import SingletonMeta, SingletonBase, ResourceManager

__all__ = [
    # Constants
    'APP_NAME',
    'APP_VERSION', 
    'APP_DESCRIPTION',
    'SUPPORTED_EXTENSIONS',
    'MAX_FILE_SIZE_MB',
    'UUID_PATTERN', 
    'DATABASE_NAME',
    'DATABASE_TIMEOUT',
    'BATCH_INSERT_SIZE',
    'DEFAULT_WINDOW_SIZE',
    'MIN_WINDOW_SIZE',
    'THUMBNAIL_SIZE',
    'LIST_ITEM_HEIGHT', 
    'MAX_WORKER_THREADS',
    'IMAGE_CACHE_SIZE',
    'SCAN_BATCH_SIZE',
    'THEME_COLORS',
    'FONTS',
    'get_default_scan_directories',
    
    # Exceptions
    'UdioManagerError',
    'ConfigurationError', 
    'DatabaseError',
    'FileSystemError',
    'ScanError',
    'MetadataParseError',
    'TrackValidationError',
    'AudioPlaybackError',
    'ImageProcessingError', 
    'ExportError',
    'DependencyError',
    'CancellationError',
    'ResourceCleanupError',
    
    # Singleton Pattern
    'SingletonMeta',
    'SingletonBase', 
    'ResourceManager',
]