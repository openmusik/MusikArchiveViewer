# udio_media_manager/src/udio_media_manager/__main__.py - CORRECTED VERSION
"""
Executable Entry Point for the Udio Media Manager Package.

This script serves as the primary entry point when the package is executed as a
module (e.g., `python -m udio_media_manager`).
"""
import sys

def run() -> None:
    """
    Imports the core Application class, instantiates it, and runs it.
    This delegates all application logic to a centralized location.
    """
    try:
        # Correctly import the Application class
        from .core.app import Application
        
        # Create an instance and run it
        app = Application()
        app.run()
        
    except ImportError as e:
        print(f"FATAL ERROR: Failed to import application components: {e}", file=sys.stderr)
        print("Please ensure all dependencies are installed and the project structure is correct.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during application startup: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


# This standard guard ensures that the `run()` function is called only when
# the script is executed.
if __name__ == "__main__":
    run()