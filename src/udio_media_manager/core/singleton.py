# upgraded_singleton.py

"""
Singleton pattern implementation for managing shared resources.
"""

import threading
import logging
from typing import Dict, Any, Type, TypeVar

# It's good practice to get a logger even in utility modules
logger = logging.getLogger(__name__)

T = TypeVar('T')


class SingletonMeta(type):
    """
    Thread-safe implementation of the Singleton pattern using a metaclass.
    This ensures that only one instance of a class exists throughout the
    application's lifecycle, even with nested singleton creation.
    """
    
    _instances: Dict[Type, Any] = {}
    # UPGRADE 1: The lock MUST be a Re-entrant Lock (RLock).
    # This prevents deadlocks if one singleton's __init__ creates another singleton.
    _lock: threading.RLock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        """
        Create or return the singleton instance. This method is now safe
        from deadlocks caused by nested singleton instantiation.
        """
        with cls._lock:
            if cls not in cls._instances:
                # This call might trigger another singleton creation, which is
                # now safe because the lock is re-entrant.
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class SingletonBase(metaclass=SingletonMeta):
    """
    UPGRADE 2: Renamed from SingletonBase for clarity.
    
    A base class for singletons providing a standardized shutdown mechanism
    and a convenient instance-level lock for thread-safe operations.
    """
    
    def __init__(self):
        """
        Initializes the singleton instance. The _shutdown flag is used to
        prevent operations on a service that has already been shut down.
        """
        self._shutdown = False
        # Each instance gets its own RLock for managing its internal state.
        self._instance_lock = threading.RLock()
        
    def shutdown(self):
        """
        Marks the singleton as shut down. Subclasses should override this to
        perform cleanup of resources (e.g., closing files, connections)
        before calling the super().shutdown() method.
        """
        with self._instance_lock:
            logger.debug(f"Shutting down {self.__class__.__name__}")
            self._shutdown = True
    
    @property
    def is_shutdown(self) -> bool:
        """Checks if the singleton has been shut down."""
        with self._instance_lock:
            return self._shutdown


class ResourceManager(SingletonBase):
    """
    A central manager for application-wide shared resources.
    Provides a thread-safe way to register, access, and clean up resources.
    """
    
    def __init__(self):
        super().__init__()
        self._resources: Dict[str, Any] = {}
        
    def register_resource(self, name: str, resource: Any) -> None:
        """
        Registers a shared resource.
        
        Args:
            name: A unique identifier for the resource.
            resource: The resource object to register.
        """
        with self._instance_lock:
            if name in self._resources:
                logger.warning(f"Resource '{name}' is already registered. Overwriting.")
            self._resources[name] = resource
            
    def get_resource(self, name: str) -> Any:
        """
        Retrieves a registered resource by its name.
        
        Raises:
            KeyError: If the resource is not registered.
        """
        # No lock needed for reads if writes are locked, but locking is safer
        # and overhead is minimal.
        with self._instance_lock:
            if name not in self._resources:
                raise KeyError(f"Resource '{name}' is not registered")
            return self._resources[name]
            
    def unregister_resource(self, name: str) -> None:
        """
        Unregisters a resource and calls its shutdown() method if it exists.
        """
        with self._instance_lock:
            if name in self._resources:
                resource = self._resources.pop(name) # pop removes and returns
                if hasattr(resource, 'shutdown') and callable(resource.shutdown):
                    try:
                        logger.debug(f"Shutting down resource: {name}")
                        resource.shutdown()
                    except Exception as e:
                        # UPGRADE 3: Log errors instead of silently passing.
                        logger.error(f"Error during shutdown of resource '{name}': {e}", exc_info=True)
                
    def has_resource(self, name: str) -> bool:
        """Checks if a resource is registered."""
        with self._instance_lock:
            return name in self._resources
            
    def shutdown(self):
        """Shuts down all registered resources before shutting down itself."""
        logger.info("ResourceManager shutting down all registered resources...")
        with self._instance_lock:
            # Iterating over a copy of the keys is crucial because
            # unregister_resource modifies the dictionary.
            for name in list(self._resources.keys()):
                self.unregister_resource(name)
        super().shutdown()
        logger.info("ResourceManager shutdown complete.")