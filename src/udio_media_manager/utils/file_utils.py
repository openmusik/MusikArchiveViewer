"""
File system utilities for Udio Media Manager.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.exceptions import FileSystemError
from ..core.constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB
from ..domain.enums import FileType
from ..utils.logging import get_logger


logger = get_logger(__name__)


class FileUtils:
    """
    Utility class for file system operations with error handling and performance optimizations.
    """
    
    @staticmethod
    def safe_read_text(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """
        Safely read text from a file with comprehensive error handling.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding to use
            
        Returns:
            File content as string, or None if reading fails
            
        Raises:
            FileSystemError: If file is too large or other critical error occurs
        """
        try:
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return None
                
            # Check file size before reading
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise FileSystemError(
                    f"File too large: {file_size / (1024*1024):.1f}MB > {MAX_FILE_SIZE_MB}MB",
                    path=file_path,
                    operation="read"
                )
                
            return file_path.read_text(encoding=encoding, errors='ignore')
            
        except (OSError, PermissionError, UnicodeError) as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return None
        except Exception as e:
            raise FileSystemError(
                f"Unexpected error reading file: {e}",
                path=file_path,
                operation="read"
            ) from e
            
    @staticmethod
    def safe_write_text(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """
        Safely write text to a file with backup and atomic operations.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: Text encoding to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            temp_path.write_text(content, encoding=encoding)
            
            # Replace original file
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                file_path.replace(backup_path)
                
            temp_path.replace(file_path)
            return True
            
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error writing file {file_path}: {e}")
            return False
            
    @staticmethod
    def get_file_hash(file_path: Path, algorithm: str = 'md5') -> Optional[str]:
        """
        Calculate file hash for change detection.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256')
            
        Returns:
            File hash as hex string, or None if calculation fails
        """
        try:
            if not file_path.exists():
                return None
                
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
                    
            return hash_func.hexdigest()
            
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return None
            
    @staticmethod
    def find_files_by_pattern(
        directory: Path,
        patterns: List[str],
        recursive: bool = True
    ) -> List[Path]:
        """
        Find files matching glob patterns.
        
        Args:
            directory: Directory to search in
            patterns: List of glob patterns
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        matches = set()
        
        try:
            for pattern in patterns:
                if recursive:
                    matches.update(directory.rglob(pattern))
                else:
                    matches.update(directory.glob(pattern))
                    
            return sorted(matches)
            
        except (OSError, PermissionError) as e:
            raise FileSystemError(
                f"Error searching directory: {e}",
                path=directory,
                operation="search"
            ) from e
            
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """
        Get file size in bytes with error handling.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or 0 if file doesn't exist or error occurs
        """
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except (OSError, PermissionError):
            return 0
            
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        """
        Calculate total size of all files in a directory.
        
        Args:
            directory: Directory to calculate size for
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += FileUtils.get_file_size(file_path)
            return total_size
            
        except (OSError, PermissionError) as e:
            logger.warning(f"Error calculating directory size {directory}: {e}")
            return total_size
            
    @staticmethod
    def group_files_by_uuid(directory: Path, recursive: bool = True) -> Dict[str, Dict[FileType, Path]]:
        """
        Group files by UUID found in filenames.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively
            
        Returns:
            Dictionary mapping UUIDs to file type -> path mappings
        """
        import re
        
        uuid_pattern = re.compile(r"\[([a-f0-9-]{36})\]", re.IGNORECASE)
        file_groups: Dict[str, Dict[FileType, Path]] = {}
        
        try:
            # Get all supported files
            all_files = FileUtils.find_files_by_pattern(
                directory,
                [f"*{ext}" for ext in SUPPORTED_EXTENSIONS],
                recursive
            )
            
            for file_path in all_files:
                if match := uuid_pattern.search(file_path.name):
                    song_id = match.group(1).lower()
                    
                    try:
                        file_type = FileType.from_extension(file_path.suffix)
                        file_groups.setdefault(song_id, {})[file_type] = file_path
                    except ValueError:
                        # Skip unsupported file extensions
                        continue
                        
            return file_groups
            
        except Exception as e:
            raise FileSystemError(
                f"Error grouping files by UUID: {e}",
                path=directory,
                operation="group_files"
            ) from e
            
    @staticmethod
    def cleanup_empty_directories(directory: Path) -> int:
        """
        Remove empty directories recursively.
        
        Args:
            directory: Root directory to clean up
            
        Returns:
            Number of directories removed
        """
        removed_count = 0
        
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                current_dir = Path(root)
                
                # Skip if directory contains files or we're at the root
                if any(current_dir.iterdir()) or current_dir == directory:
                    continue
                    
                try:
                    current_dir.rmdir()
                    removed_count += 1
                    logger.debug(f"Removed empty directory: {current_dir}")
                except OSError:
                    # Directory not empty or permission error
                    continue
                    
            return removed_count
            
        except Exception as e:
            logger.warning(f"Error cleaning up empty directories: {e}")
            return removed_count
            
    @staticmethod
    def copy_file_with_progress(
        source: Path,
        destination: Path,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Copy file with progress reporting.
        
        Args:
            source: Source file path
            destination: Destination file path
            progress_callback: Callback for progress updates (bytes_copied, total_bytes)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not source.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
                
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            total_size = source.stat().st_size
            bytes_copied = 0
            
            with open(source, 'rb') as src, open(destination, 'wb') as dst:
                while True:
                    chunk = src.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                        
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    if progress_callback:
                        progress_callback(bytes_copied, total_size)
                        
            # Verify copy
            if destination.stat().st_size == total_size:
                return True
            else:
                logger.error(f"File copy verification failed: {source} -> {destination}")
                try:
                    destination.unlink()
                except OSError:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Error copying file {source} -> {destination}: {e}")
            return False
            
    @staticmethod
    def batch_operation(
        files: List[Path],
        operation: callable,
        max_workers: int = 4,
        **kwargs
    ) -> Tuple[int, int, List[Tuple[Path, Exception]]]:
        """
        Perform batch file operations with parallel processing.
        
        Args:
            files: List of files to process
            operation: Function to call for each file (should take Path as first arg)
            max_workers: Maximum number of worker threads
            **kwargs: Additional arguments to pass to operation
            
        Returns:
            Tuple of (success_count, failure_count, errors_list)
        """
        success_count = 0
        failure_count = 0
        errors: List[Tuple[Path, Exception]] = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(operation, file_path, **kwargs): file_path 
                for file_path in files
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append((file_path, e))
                    logger.warning(f"Batch operation failed for {file_path}: {e}")
                    
        return success_count, failure_count, errors


class PathValidator:
    """
    Utility class for validating file paths and permissions.
    """
    
    @staticmethod
    def is_valid_directory(path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if path is a valid, accessible directory.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not path.exists():
                return False, "Path does not exist"
                
            if not path.is_dir():
                return False, "Path is not a directory"
                
            # Test read permission
            try:
                next(path.iterdir(), None)
            except PermissionError:
                return False, "No read permission for directory"
                
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {e}"
            
    @staticmethod
    def is_supported_file_type(file_path: Path) -> bool:
        """
        Check if file has supported extension.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file type is supported
        """
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS
        
    @staticmethod
    def has_write_permission(directory: Path) -> bool:
        """
        Check if we have write permission for directory.
        
        Args:
            directory: Directory to check
            
        Returns:
            True if write permission is available
        """
        try:
            test_file = directory / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False
            
    @staticmethod
    def get_available_space(path: Path) -> int:
        """
        Get available disk space in bytes.
        
        Args:
            path: Path to check space for
            
        Returns:
            Available space in bytes, or 0 if unable to determine
        """
        try:
            import shutil
            return shutil.disk_usage(path).free
        except (OSError, AttributeError):
            return 0


class FileOrganizer:
    """
    Utilities for organizing Udio track files.
    """
    
    @staticmethod
    def create_organized_structure(
        source_dir: Path,
        dest_dir: Path,
        organize_by: str = "artist"  # "artist", "date", "album"
    ) -> int:
        """
        Organize Udio tracks into a structured directory layout.
        
        Args:
            source_dir: Source directory with Udio files
            dest_dir: Destination directory for organized structure
            organize_by: Organization scheme
            
        Returns:
            Number of files organized
        """
        # This would be implemented based on specific organization needs
        # For now, return stub implementation
        logger.info(f"Organizing files from {source_dir} to {dest_dir} by {organize_by}")
        return 0