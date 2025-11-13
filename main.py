# udio_media_manager/main.py - DEFINITIVE & FULLY-FEATURED VERSION

"""
Enhanced Main Entry Point for Udio Media Manager.
Robust bootstrap with comprehensive error handling and import resolution.
"""

import sys
import os
import argparse
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src to path immediately to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# --- Bootstrap Configuration ---
BOOTSTRAP_LOGGER_NAME = "Bootstrap"
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class ImportResolver:
    """Handles dynamic import resolution."""
    @staticmethod
    def resolve_module(module_path: str, class_name: str = None):
        try:
            if class_name:
                module = __import__(module_path, fromlist=[class_name])
                return getattr(module, class_name)
            else:
                return __import__(module_path)
        except ImportError as e:
            raise ImportError(f"Failed to import {module_path}{f'.{class_name}' if class_name else ''}: {e}")

class BootstrapManager:
    """Manages the application bootstrap process with comprehensive error handling."""
    
    def __init__(self):
        self.logger: Optional[logging.Logger] = None
        self.args: Optional[argparse.Namespace] = None
        self.import_resolver = ImportResolver()
        
    def setup_bootstrap_logging(self, level: str = DEFAULT_LOG_LEVEL):
        """Sets up an enhanced bootstrap logger."""
        logger = logging.getLogger(BOOTSTRAP_LOGGER_NAME)
        for handler in logger.handlers[:]: logger.removeHandler(handler)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] Bootstrap: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        logger.propagate = False
        self.logger = logger

    def parse_arguments(self):
        """Parses comprehensive command-line arguments with validation."""
        parser = argparse.ArgumentParser(description="Udio Media Manager")
        
        # Logging arguments
        logging_group = parser.add_argument_group('Logging Options')
        logging_group.add_argument("--log-level", default=DEFAULT_LOG_LEVEL, choices=SUPPORTED_LOG_LEVELS, help="Set bootstrap logging level.")
        logging_group.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v for INFO, -vv for DEBUG).")
        
        # Debugging arguments
        debug_group = parser.add_argument_group('Debugging Options')
        debug_group.add_argument("--debug-imports", action="store_true", help="Debug import issues and module structure.")
        debug_group.add_argument("--auto-fix", action="store_true", help="Automatically fix common known import issues.")
        
        self.args = parser.parse_args()
        
        # Handle verbosity levels
        if self.args.verbose >= 2:
            self.args.log_level = "DEBUG"
        elif self.args.verbose >= 1:
            self.args.log_level = "INFO"

    def setup_application_paths(self) -> bool:
        """Configures Python paths and validates project structure."""
        self.logger.info("Setting up application paths...")
        try:
            if not SRC_PATH.exists() or not (SRC_PATH / "udio_media_manager").exists():
                self.logger.error("❌ 'src/udio_media_manager' directory not found. Please run from the project root.")
                return False
            if not self._test_critical_imports():
                return False
            self.logger.info("✅ Path configuration completed.")
            return True
        except Exception as e:
            self.logger.error(f"❌ Path setup failed: {e}", exc_info=self.logger.level == logging.DEBUG)
            return False

    def _test_critical_imports(self) -> bool:
        """Test critical imports to ensure they work."""
        critical_imports = [
            ('udio_media_manager.core.app', 'Application'),
            ('udio_media_manager.core.constants', 'APP_VERSION'),
        ]
        all_successful = True
        for module_path, name in critical_imports:
            try:
                self.import_resolver.resolve_module(module_path, name)
                self.logger.debug(f"✅ {module_path}.{name} imported successfully.")
            except ImportError as e:
                self.logger.error(f"❌ Failed to import {module_path}.{name}: {e}")
                all_successful = False
        return all_successful

    def _debug_imports(self):
        """Prints diagnostic information about the Python import path."""
        self.logger.info("--- Import Debug Information ---")
        self.logger.debug("Python Path (sys.path):")
        for i, path in enumerate(sys.path):
            self.logger.debug(f"  [{i}]: {path}")
        self.logger.info("---------------------------------")


    def initialize_application(self) -> bool:
        """Imports and initializes the main application."""
        self.logger.info("🚀 Initializing application...")
        try:
            App = self.import_resolver.resolve_module('udio_media_manager.core.app', 'Application')
            # Pass CLI arguments to the Application instance
            app_instance = App(**vars(self.args))
            app_instance.run()
            return True
        except ImportError as e:
            self.logger.error(f"❌ Failed to import application modules: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during application startup: {e}", exc_info=self.logger.level == logging.DEBUG)
            return False

    def run(self) -> int:
        """Executes the complete bootstrap sequence."""
        self.parse_arguments()
        self.setup_bootstrap_logging(self.args.log_level)
        self.logger.info("=" * 60)
        self.logger.info("🎵 Udio Media Manager - Enhanced Bootstrap")
        self.logger.info("=" * 60)

        if self.args.debug_imports:
            self._debug_imports()
        
        if not self.setup_application_paths():
            return 1
            
        if not self.initialize_application():
            return 1
            
        self.logger.info("✅ Application shutdown sequence initiated by bootstrap.")
        return 0

def main_entry() -> int:
    """Main entry point with top-level error handling."""
    bootstrap = BootstrapManager()
    try:
        return bootstrap.run()
    except Exception as e:
        print(f"💥 CRITICAL BOOTSTRAP FAILURE: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main_entry())