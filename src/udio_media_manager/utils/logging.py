# logging.py - With Quiet Mode

"""
Quiet logging configuration for Udio Media Manager.

This module provides intelligent logging that suppresses repetitive success messages
and only shows important information after the first few instances.
"""

import logging
import logging.handlers
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict

from ..core.singleton import SingletonBase
from ..core.exceptions import ConfigurationError


class QuietFilter(logging.Filter):
    """
    Filter that suppresses repetitive success messages after a threshold.
    """
    
    def __init__(self, name: str = "", success_threshold: int = 5):
        super().__init__(name)
        self.success_threshold = success_threshold
        self.success_counts = defaultdict(int)
        self.suppressed_messages = defaultdict(int)
        
    def filter(self, record: logging.LogRecord) -> bool:
        # Always show warnings and errors
        if record.levelno >= logging.WARNING:
            return True
            
        # For INFO messages, check if they're repetitive successes
        if record.levelno == logging.INFO:
            message = record.getMessage()
            
            # Check if this is a success message (common patterns)
            is_success = any(pattern in message for pattern in [
                "✅", "Successfully", "completed successfully", "loaded successfully",
                "parsed successfully", "built successfully", "initialized successfully",
                "retrieved", "displaying", "found", "added", "created"
            ])
            
            if is_success:
                # Use module name as key to track per-module success counts
                module_key = record.name
                self.success_counts[module_key] += 1
                
                # Only show first few successes per module
                if self.success_counts[module_key] > self.success_threshold:
                    self.suppressed_messages[module_key] += 1
                    return False
                    
        # Show everything else
        return True


class ProgressTracker:
    """
    Tracks progress and only logs at milestones to reduce spam.
    """
    
    def __init__(self, total: int, milestone_interval: int = 100):
        self.total = total
        self.current = 0
        self.milestone_interval = milestone_interval
        self.last_milestone = 0
        
    def increment(self) -> bool:
        """
        Increment counter and return True if should log progress.
        """
        self.current += 1
        should_log = (
            self.current >= self.total or
            self.current % self.milestone_interval == 0 or
            self.current - self.last_milestone >= self.milestone_interval
        )
        
        if should_log:
            self.last_milestone = self.current
            
        return should_log
        
    def get_progress(self) -> str:
        """Get progress string."""
        return f"{self.current}/{self.total} ({self.current/self.total:.1%})"


class LogManager(SingletonBase):
    """
    Quiet logging manager that suppresses repetitive success messages.
    """
    
    def __init__(self):
        super().__init__()
        self._configured = False
        self._loggers: Dict[str, logging.Logger] = {}
        self._spam_filters: List[str] = []
        self._quiet_filter: Optional[QuietFilter] = None
        
    def configure(
        self,
        log_file: Optional[Path] = None,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        log_format: Optional[str] = None,
        enable_spam_filters: bool = True,
        enable_quiet_mode: bool = True,
        success_threshold: int = 3  # Show only first 3 successes per module
    ) -> None:
        """
        Configure quiet logging that suppresses repetitive success messages.
        """
        with self._instance_lock:
            if self._configured:
                return
                
            if log_file is None:
                log_file = Path(tempfile.gettempdir()) / "udio_media_manager.log"
                
            if log_format is None:
                log_format = (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                
            formatter = logging.Formatter(log_format)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Console handler with quiet filter
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)
            
            # Add quiet filter to suppress repetitive successes
            if enable_quiet_mode:
                self._quiet_filter = QuietFilter(success_threshold=success_threshold)
                console_handler.addFilter(self._quiet_filter)
            
            root_logger.addHandler(console_handler)
            
            # File handler - keep everything for debugging
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(file_level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except (OSError, PermissionError) as e:
                raise ConfigurationError(
                    f"Failed to configure file logging: {e}",
                    details=f"Log file path: {log_file}"
                )
            
            # Configure spam filters
            if enable_spam_filters:
                self._setup_spam_filters()
            
            self._configured = True
            
            # Minimal startup message
            logger = self.get_logger("LogManager")
            logger.info("🚀 Udio Media Manager Starting")
            logger.debug("Logging system initialized with quiet mode")
            
    def _setup_spam_filters(self) -> None:
        """Configure specific loggers to reduce spam."""
        spam_sources = [
            'PIL', 'Pillow', 'tkinter', 'vlc', 'mutagen', 'pygame',
            'sqlite3', 'urllib3', 'requests', 'httpcore', 'httpx',
            'asyncio', 'concurrent.futures',
        ]
        
        for spam_source in spam_sources:
            spam_logger = logging.getLogger(spam_source)
            spam_logger.setLevel(logging.WARNING)
            self._spam_filters.append(spam_source)
            
    def get_logger(self, name: str, level: Optional[int] = None) -> logging.Logger:
        """
        Get a logger with optional level override.
        """
        with self._instance_lock:
            if name not in self._loggers:
                logger = logging.getLogger(name)
                
                if level is not None:
                    logger.setLevel(level)
                    
                self._loggers[name] = logger
                
            return self._loggers[name]
            
    def get_suppression_stats(self) -> Dict[str, int]:
        """
        Get statistics about suppressed messages.
        """
        if self._quiet_filter:
            return dict(self._quiet_filter.suppressed_messages)
        return {}
        
    def reset_suppression_counts(self) -> None:
        """
        Reset suppression counts (useful after major operations).
        """
        if self._quiet_filter:
            self._quiet_filter.success_counts.clear()
            self._quiet_filter.suppressed_messages.clear()
                
    def shutdown(self):
        """Clean shutdown with suppression summary."""
        with self._instance_lock:
            # Log suppression summary if we suppressed anything
            if self._quiet_filter and self._quiet_filter.suppressed_messages:
                total_suppressed = sum(self._quiet_filter.suppressed_messages.values())
                logger = self.get_logger("LogManager")
                logger.info(f"📊 Suppressed {total_suppressed} repetitive success messages")
                
            logging.shutdown()
            self._loggers.clear()
            super().shutdown()


class LoggingContext:
    """
    Context manager for temporarily altering logging configuration.
    """
    
    def __init__(self, level: Optional[int] = None, handler: Optional[logging.Handler] = None):
        self.level = level
        self.handler = handler
        self.original_level: Optional[int] = None
        self.root_logger = logging.getLogger()
        
    def __enter__(self):
        if self.level is not None:
            self.original_level = self.root_logger.level
            self.root_logger.setLevel(self.level)
            
        if self.handler is not None:
            self.root_logger.addHandler(self.handler)
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.level is not None and self.original_level is not None:
            self.root_logger.setLevel(self.original_level)
            
        if self.handler is not None:
            self.root_logger.removeHandler(self.handler)


class BatchLogger:
    """
    Logs batch operations with progress reporting instead of individual items.
    """
    
    def __init__(self, logger: logging.Logger, operation_name: str, total_items: int):
        self.logger = logger
        self.operation_name = operation_name
        self.total_items = total_items
        self.processed = 0
        self.errors = 0
        self.progress_tracker = ProgressTracker(total_items, milestone_interval=50)
        
    def log_success(self, item_name: str = ""):
        """Log success, but only at milestones."""
        self.processed += 1
        if self.progress_tracker.increment():
            progress = self.progress_tracker.get_progress()
            self.logger.info(f"📦 {self.operation_name}: {progress}")
            
    def log_error(self, item_name: str, error: str):
        """Always log errors."""
        self.errors += 1
        self.logger.error(f"❌ {self.operation_name} failed for {item_name}: {error}")
        
    def complete(self):
        """Log completion summary."""
        if self.errors > 0:
            self.logger.warning(
                f"⚠️  {self.operation_name} completed with {self.errors} errors "
                f"({self.processed} successful)"
            )
        else:
            self.logger.info(f"✅ {self.operation_name} completed successfully")


# Convenience functions
def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a configured logger instance."""
    return LogManager().get_logger(name, level)


def setup_logging(
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_spam_filters: bool = True,
    enable_quiet_mode: bool = True,
    success_threshold: int = 3,
    **kwargs
) -> None:
    """
    Setup quiet logging that doesn't spam the console.
    """
    LogManager().configure(
        console_level=console_level,
        file_level=file_level,
        enable_spam_filters=enable_spam_filters,
        enable_quiet_mode=enable_quiet_mode,
        success_threshold=success_threshold,
        **kwargs
    )


def setup_quiet_logging():
    """
    Setup for production - very quiet console output.
    """
    setup_logging(
        console_level=logging.WARNING,  # Only show warnings and errors
        file_level=logging.INFO,        # Keep info in files
        enable_quiet_mode=True,
        success_threshold=2             # Show even fewer successes
    )


def setup_verbose_logging():
    """
    Setup for debugging - show everything.
    """
    setup_logging(
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        enable_quiet_mode=False,        # Disable quiet mode for debugging
        enable_spam_filters=False
    )


def create_batch_logger(logger_name: str, operation: str, total: int) -> BatchLogger:
    """
    Create a batch logger for processing many items without spam.
    """
    logger = get_logger(logger_name)
    return BatchLogger(logger, operation, total)


# Quick setup for common use cases
def quick_setup(quiet: bool = True):
    """
    Quick setup that's quiet by default.
    """
    if quiet:
        setup_quiet_logging()
    else:
        setup_verbose_logging()