"""
PROFESSIONAL-GRADE Image Loading and Caching Service for Udio Media Manager.

STABLE VERSION: Fixed logger reference and simplified API.
"""

import threading
import uuid
import weakref
import time
from pathlib import Path
from typing import Optional, Dict, Tuple, Callable, List, Any, Union, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
from dataclasses import dataclass, field
from enum import Enum

from ..core.singleton import SingletonBase
from ..core.exceptions import DependencyError
from ..core.constants import THUMBNAIL_SIZE, IMAGE_CACHE_SIZE
from ..utils.logging import get_logger

# TYPE_CHECKING block for static analysis
if TYPE_CHECKING:
    from PIL import Image, ImageTk

# Runtime import handling
try:
    from PIL import Image, ImageTk, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    # Create mock classes to prevent runtime errors
    class Image:
        class Image: pass
        Resampling = type('Resampling', (), {'LANCZOS': 1})
    class ImageTk:
        class PhotoImage: pass
    class ImageOps:
        @staticmethod
        def expand(*args, **kwargs): return None

# FIXED: Define logger at module level
logger = get_logger(__name__)


class RequestStatus(Enum):
    """Lifecycle status of an image loading request."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ImageRequest:
    """Represents an image loading request with all necessary context."""
    path: Path
    size: Tuple[int, int]
    callback: Callable[[Optional["ImageTk.PhotoImage"]], None]
    request_id: str
    status: RequestStatus = field(default=RequestStatus.PENDING, compare=False)
    weak_refs: List[weakref.ReferenceType] = field(default_factory=list, compare=False)
    created_time: float = field(default_factory=time.time)


class ImageLoader(SingletonBase):
    """
    STABLE VERSION: Professional, thread-safe, asynchronous image loading service.
    """

    def __init__(self, max_workers: int = 2, max_cache_size: int = IMAGE_CACHE_SIZE):
        super().__init__()
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, "ImageTk.PhotoImage"] = {}
        self._cache_keys: List[str] = []
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, 
            thread_name_prefix="ImageLoader"
        )
        self._request_queue = Queue()
        self._pending_requests: Dict[str, ImageRequest] = {}
        self._root_reference: Optional[weakref.ReferenceType] = None
        self._running = True
        self._lock = threading.RLock()
        self._request_timeout = 30.0  # 30 seconds timeout for requests
        
        # Statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'requests_processed': 0,
            'requests_failed': 0,
            'requests_cancelled': 0
        }
        
        self._worker_thread = threading.Thread(
            target=self._process_requests, 
            daemon=True, 
            name="ImageLoaderQueue"
        )
        self._worker_thread.start()
        logger.info(f"🚀 ImageLoader initialized (max_workers={max_workers}, cache_size={max_cache_size})")

    @property
    def _root(self) -> Optional[Any]:
        """Safely resolves the weak reference to the Tkinter root window."""
        return self._root_reference() if self._root_reference else None

    def set_root(self, root: Any) -> None:
        """Sets the Tkinter root window via a weak reference."""
        self._root_reference = weakref.ref(root)
        logger.debug("✅ ImageLoader root reference set")

    def load_image(
        self,
        path: Union[str, Path],
        size: Tuple[int, int] = THUMBNAIL_SIZE,
        callback: Optional[Callable] = None,
        weak_refs: Optional[List[Any]] = None
    ) -> Optional[str]:
        """
        SIMPLIFIED VERSION: Asynchronously loads an image.
        Returns request ID for cancellation.
        """
        if not path or not callback:
            logger.debug("Skipping image load: missing path or callback")
            return None

        # Validate and convert path
        image_path = self._validate_and_convert_path(path)
        if not image_path:
            self._schedule_callback(callback, None, weak_refs)
            return None

        # Check cache first
        cache_key = self._get_cache_key(image_path, size)
        with self._lock:
            if cache_key in self._cache:
                cached_image = self._cache[cache_key]
                # Update LRU order
                self._cache_keys.remove(cache_key)
                self._cache_keys.append(cache_key)
                self._stats['cache_hits'] += 1
                logger.debug(f"🔥 Cache hit for {image_path.name}")
                self._schedule_callback(callback, cached_image, weak_refs)
                return None

        self._stats['cache_misses'] += 1
        
        # Create new request
        request_id = str(uuid.uuid4())
        
        safe_weak_refs = self._create_safe_weak_refs(weak_refs)
        
        request = ImageRequest(
            path=image_path,
            size=size,
            callback=callback,
            request_id=request_id,
            weak_refs=safe_weak_refs
        )
        
        with self._lock:
            self._pending_requests[request_id] = request
        
        self._request_queue.put(request)
        logger.debug(f"📥 Queued image request: {image_path.name} (ID: {request_id[:8]})")
        return request_id

    def _schedule_callback(self, callback: Callable, image: Optional["ImageTk.PhotoImage"], weak_refs: Optional[List[Any]]) -> None:
        """Schedules callback execution on main thread."""
        if not callback:
            return
            
        if self._root:
            self._root.after_idle(lambda: self._execute_callback(callback, image, weak_refs))
        else:
            # Fallback: execute directly
            self._execute_callback(callback, image, weak_refs)

    def _execute_callback(self, callback: Callable, image: Optional["ImageTk.PhotoImage"], weak_refs: Optional[List[Any]]) -> None:
        """Executes callback with weak reference validation."""
        # Check if any weak references are now None (objects destroyed)
        if weak_refs:
            valid_refs = all(ref() is not None for ref in weak_refs)
            if not valid_refs:
                logger.debug("🔄 Callback skipped: target widgets no longer exist")
                return
                
        try:
            callback(image)
        except Exception as e:
            logger.error(f"❌ Error in image callback: {e}")

    def _create_safe_weak_refs(self, objects: Optional[List[Any]]) -> List[weakref.ReferenceType]:
        """Safely creates weak references."""
        if not objects:
            return []
            
        weak_refs = []
        for obj in objects:
            try:
                if isinstance(obj, weakref.ReferenceType):
                    weak_refs.append(obj)
                elif obj is not None:
                    weak_refs.append(weakref.ref(obj))
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not create weak reference for {type(obj)}: {e}")
                
        return weak_refs

    def _validate_and_convert_path(self, path: Union[str, Path]) -> Optional[Path]:
        """Validates and converts input path to a Path object."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"🚫 Image path does not exist: {path_obj}")
                return None
            return path_obj.resolve()
        except (TypeError, ValueError, OSError) as e:
            logger.error(f"❌ Invalid path provided: {path} ({e})")
            return None

    def cancel_request(self, request_id: str) -> bool:
        """Cancels a pending image request."""
        with self._lock:
            if request := self._pending_requests.get(request_id):
                if request.status in [RequestStatus.PENDING, RequestStatus.PROCESSING]:
                    request.status = RequestStatus.CANCELLED
                    self._stats['requests_cancelled'] += 1
                    logger.debug(f"🛑 Cancelled image request: {request_id[:8]}")
                    return True
        return False

    def _get_cache_key(self, path: Path, size: Tuple[int, int]) -> str:
        """Generates a unique key for caching."""
        return f"{path}|{size[0]}x{size[1]}"

    def _process_requests(self) -> None:
        """Worker thread loop."""
        while self._running:
            try:
                # Cleanup stale requests
                self._cleanup_stale_requests()
                
                # Get next request
                request = self._request_queue.get(timeout=1.0)
                if request is None:  # Shutdown signal
                    break

                with self._lock:
                    if request.status == RequestStatus.CANCELLED:
                        self._request_queue.task_done()
                        continue
                    request.status = RequestStatus.PROCESSING
                
                logger.debug(f"🔄 Processing image: {request.path.name}")
                
                # Submit to thread pool
                future = self._executor.submit(
                    self._load_and_process_image, 
                    request.path, 
                    request.size
                )
                future.add_done_callback(lambda f, r=request: self._on_processing_complete(f, r))

            except Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error in image request processing loop: {e}")

    def _cleanup_stale_requests(self) -> None:
        """Clean up requests that have been pending too long."""
        current_time = time.time()
        stale_requests = []
        
        with self._lock:
            for request_id, request in self._pending_requests.items():
                if (current_time - request.created_time) > self._request_timeout:
                    stale_requests.append(request_id)
            
            for request_id in stale_requests:
                request = self._pending_requests.pop(request_id, None)
                if request:
                    request.status = RequestStatus.CANCELLED
                    self._stats['requests_cancelled'] += 1
                    logger.warning(f"🕒 Cancelled stale request: {request_id[:8]}")

    def _on_processing_complete(self, future: Future, request: ImageRequest) -> None:
        """Callback executed when image processing is complete."""
        with self._lock:
            if request.status == RequestStatus.CANCELLED:
                self._request_queue.task_done()
                return

        try:
            pil_image: Optional["Image.Image"] = future.result()
            request.status = RequestStatus.COMPLETED if pil_image else RequestStatus.FAILED
            
            if request.status == RequestStatus.FAILED:
                self._stats['requests_failed'] += 1
                logger.warning(f"❌ Failed to process image: {request.path.name}")
            else:
                self._stats['requests_processed'] += 1

            # Schedule finalization on main thread
            if self._root:
                self._root.after_idle(self._finalize_request, request, pil_image)
            else:
                self._finalize_request(request, pil_image)

        except Exception as e:
            logger.error(f"❌ Error in processing complete callback for {request.path.name}: {e}")
            request.status = RequestStatus.FAILED
            self._stats['requests_failed'] += 1
            if self._root:
                self._root.after_idle(self._finalize_request, request, None)
        finally:
            self._request_queue.task_done()

    def _finalize_request(self, request: ImageRequest, pil_image: Optional["Image.Image"]) -> None:
        """Executed on main UI thread. Creates PhotoImage and calls callback."""
        # Double-check cancellation
        with self._lock:
            if request.status == RequestStatus.CANCELLED:
                if request.request_id in self._pending_requests:
                    del self._pending_requests[request.request_id]
                return

        tk_image: Optional["ImageTk.PhotoImage"] = None
        
        if pil_image and HAS_PIL:
            try:
                # Create Tkinter object on main thread
                tk_image = ImageTk.PhotoImage(pil_image)
                cache_key = self._get_cache_key(request.path, request.size)
                self._cache_image(cache_key, tk_image)
                logger.debug(f"✅ Created PhotoImage for: {request.path.name}")
            except Exception as e:
                logger.error(f"❌ Failed to create PhotoImage for {request.path.name}: {e}")
                self._stats['requests_failed'] += 1

        # Execute callback
        if request.callback:
            self._execute_callback(request.callback, tk_image, request.weak_refs)

        # Clean up request
        with self._lock:
            if request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]

    def _load_and_process_image(self, path: Path, size: Tuple[int, int]) -> Optional["Image.Image"]:
        """Loads and processes image file."""
        if not HAS_PIL:
            raise DependencyError("Pillow is required for image processing.")

        # Find actual image file
        image_path = self._find_actual_image_path(path)
        if not image_path:
            return None

        try:
            with Image.open(image_path) as img:
                # Convert to compatible format
                if img.mode in ('P', 'RGBA', 'LA', 'CMYK'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Add subtle border
                img_with_border = ImageOps.expand(img, border=1, fill='#666666')
                
                return img_with_border
                
        except Exception as e:
            logger.error(f"❌ Failed to load/process image {image_path.name}: {e}")
            return None

    def _find_actual_image_path(self, path: Path) -> Optional[Path]:
        """Finds the actual image file, handling sidecar artwork."""
        # If path is already an image file
        if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.avif', '.webp'}:
            return path if path.exists() else None
            
        # Look for sidecar artwork
        possible_names = [
            f"{path.stem} - Artwork.avif",
            f"{path.stem} - Artwork.jpg", 
            f"{path.stem} - Artwork.png",
            "Artwork.avif",
            "Artwork.jpg",
            "Artwork.png",
        ]
        
        for name in possible_names:
            artwork_path = path.parent / name
            if artwork_path.exists():
                return artwork_path
                
        logger.debug(f"🎨 No artwork found for: {path.name}")
        return None

    def _cache_image(self, key: str, image: "ImageTk.PhotoImage") -> None:
        """LRU cache management."""
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                self._cache_keys.remove(key)
            
            # Add to cache
            self._cache[key] = image
            self._cache_keys.append(key)
            
            # Enforce cache size limit
            while len(self._cache_keys) > self.max_cache_size:
                oldest_key = self._cache_keys.pop(0)
                if oldest_key in self._cache:
                    del self._cache[oldest_key]

    def get_stats(self) -> Dict[str, int]:
        """Returns current statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'cache_size': len(self._cache),
                'pending_requests': len(self._pending_requests),
                'queue_size': self._request_queue.qsize()
            })
            return stats

    def clear_cache(self) -> None:
        """Clears the entire image cache."""
        with self._lock:
            cache_size = len(self._cache)
            self._cache.clear()
            self._cache_keys.clear()
            logger.info(f"🧹 Image cache cleared ({cache_size} images removed)")

    def shutdown(self):
        """Graceful shutdown."""
        if not self._running:
            return
            
        logger.info("🛑 Shutting down ImageLoader...")
        self._running = False
        
        # Cancel all pending requests
        with self._lock:
            for request in self._pending_requests.values():
                request.status = RequestStatus.CANCELLED
        
        # Signal worker to exit
        self._request_queue.put(None)
        
        # Shutdown executor
        self._executor.shutdown(wait=True, cancel_futures=True)
        
        # Wait for worker thread
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)
            
        # Clear cache
        self.clear_cache()
        
        logger.info("✅ ImageLoader shutdown complete.")
        super().shutdown()