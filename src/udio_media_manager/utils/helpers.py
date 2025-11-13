"""
General helper utilities for Udio Media Manager.
"""

import time
import functools
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from pathlib import Path

from ..utils.logging import get_logger


logger = get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class Timer:
    """
    Context manager for timing code execution.
    """
    
    def __init__(self, name: str = "Operation", logger_instance = None):
        self.name = name
        self.logger = logger_instance or logger
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.logger.debug(f"Completed: {self.name} in {duration:.3f}s")
        
    @property
    def duration(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_instance = None
):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry on
        logger_instance: Logger to use for messages
    """
    log = logger_instance or logger
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        log.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    log.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            # This should never be reached, but for type safety
            raise last_exception  # type: ignore
            
        return wrapper
    return decorator


def singleton(cls: T) -> T:
    """
    Simple singleton decorator for classes.
    
    Args:
        cls: Class to make singleton
        
    Returns:
        Singleton class instance
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
        
    return get_instance  # type: ignore


class Throttler:
    """
    Rate limiter for function calls.
    """
    
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
        self._lock = threading.Lock()
        
    def __call__(self, func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> R:
            with self._lock:
                current_time = time.time()
                time_since_last_call = current_time - self.last_call_time
                
                if time_since_last_call < self.min_interval:
                    sleep_time = self.min_interval - time_since_last_call
                    time.sleep(sleep_time)
                    
                self.last_call_time = time.time()
                
            return func(*args, **kwargs)
        return wrapper


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if not seconds or seconds < 0:
        return "--:--"
        
    minutes = int(seconds // 60)
    seconds_remaining = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes:02d}:{seconds_remaining:02d}"
    else:
        hours = minutes // 60
        minutes_remaining = minutes % 60
        return f"{hours}:{minutes_remaining:02d}:{seconds_remaining:02d}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
        
    precision = 0 if i == 0 else 1  # No decimal for bytes, 1 decimal for others
    return f"{size:.{precision}f} {size_names[i]}"


def safe_get(dictionary: Dict[Any, Any], keys: Union[str, List[str]], default: Any = None) -> Any:
    """
    Safely get nested dictionary values.
    
    Args:
        dictionary: Dictionary to search
        keys: Single key or list of nested keys
        default: Default value if key not found
        
    Returns:
        Value if found, default otherwise
    """
    if isinstance(keys, str):
        keys = [keys]
        
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
            
    return current


@contextmanager
def temporary_chdir(path: Path):
    """
    Context manager for temporarily changing working directory.
    
    Args:
        path: Directory to change to
    """
    import os
    
    original_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_cwd)


class Cache:
    """
    Simple in-memory cache with TTL support.
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cache value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self._lock:
            expire_time = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expire_time)
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get cached value.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                return default
                
            value, expire_time = self._cache[key]
            if time.time() > expire_time:
                del self._cache[key]
                return default
                
            return value
            
    def delete(self, key: str) -> bool:
        """
        Delete cached value.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
            
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expire_time) in self._cache.items()
                if current_time > expire_time
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource file.
    
    Args:
        relative_path: Relative path from project root
        
    Returns:
        Absolute Path object
    """
    project_root = Path(__file__).parent.parent.parent
    return project_root / relative_path


def is_main_thread() -> bool:
    """
    Check if current thread is main thread.
    
    Returns:
        True if current thread is main thread
    """
    return threading.current_thread() is threading.main_thread()


def run_in_main_thread(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to ensure function runs in main thread (for UI operations).
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> R:
        if is_main_thread():
            return func(*args, **kwargs)
        else:
            # This would need to be implemented with the specific UI framework
            # For now, just log a warning
            logger.warning(f"Function {func.__name__} should be called from main thread")
            return func(*args, **kwargs)
    return wrapper