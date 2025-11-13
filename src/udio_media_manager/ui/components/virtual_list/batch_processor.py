"""
Enhanced Batch Processor with Better Performance
"""

import time
import threading
from typing import List, Callable, Optional, Any
from concurrent.futures import Future, ThreadPoolExecutor

from .base import VirtualListItem
from udio_media_manager.utils.logging import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """
    Handles batched processing of virtual list items with performance optimizations.
    """
    
    def __init__(
        self,
        virtual_list,
        batch_size: int = 100,
        max_concurrent_batches: int = 2,
        processing_delay: float = 0.1
    ):
        self.virtual_list = virtual_list
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.processing_delay = processing_delay
        
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="BatchProcessor"
        )
        self._active_futures = set()
        self._cancel_event = threading.Event()
        self._processing = False
        
        logger.debug(f"🔄 BatchProcessor initialized (batch_size={batch_size}, max_batches={max_concurrent_batches})")

    def process_items(self, items: List[VirtualListItem]) -> None:
        """
        Process items in batches with priority for visible items.
        """
        if self._cancel_event.is_set() or not items:
            return
            
        self._processing = True
        total_items = len(items)
        
        logger.info(f"🔄 Processing {total_items} items in batches of {self.batch_size}")
        
        # Calculate batches
        num_batches = (total_items + self.batch_size - 1) // self.batch_size
        batches_to_process = min(num_batches, self.max_concurrent_batches)
        
        logger.info(f"📋 Queued {batches_to_process} batches")
        
        # Process initial batches
        for batch_num in range(batches_to_process):
            if self._cancel_event.is_set():
                break
                
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_items)
            
            future = self._executor.submit(self._process_batch, items, start_idx, end_idx, batch_num)
            self._active_futures.add(future)
            future.add_done_callback(self._on_batch_complete)
            
            # Small delay between batch starts to prevent UI freeze
            if batch_num < batches_to_process - 1:
                time.sleep(0.05)

    def _process_batch(self, items: List[VirtualListItem], start_idx: int, end_idx: int, batch_num: int) -> None:
        """
        Process a single batch of items.
        """
        if self._cancel_event.is_set():
            return
            
        batch_start_time = time.time()
        batch_items = items[start_idx:end_idx]
        
        try:
            # Pre-process items (this is where widget creation would happen)
            processed_count = 0
            for i, item in enumerate(batch_items):
                if self._cancel_event.is_set():
                    break
                    
                # Simulate some processing work
                # In a real implementation, this would create widgets or prepare data
                processed_count += 1
                
                # Yield occasionally to prevent blocking
                if processed_count % 10 == 0:
                    time.sleep(0.001)
            
            batch_time = time.time() - batch_start_time
            logger.debug(f"✅ Batch {batch_num} processed {processed_count} items in {batch_time:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ Error processing batch {batch_num}: {e}")

    def _on_batch_complete(self, future: Future) -> None:
        """
        Handle batch completion.
        """
        try:
            self._active_futures.discard(future)
            
            # Check if we should process more batches
            if not self._cancel_event.is_set() and len(self._active_futures) == 0:
                logger.debug("✅ All batches completed")
                
        except Exception as e:
            logger.error(f"❌ Error in batch completion: {e}")

    def cancel_processing(self) -> None:
        """
        Cancel all ongoing processing.
        """
        self._cancel_event.set()
        
        # Cancel futures
        for future in list(self._active_futures):
            future.cancel()
        self._active_futures.clear()
        
        self._processing = False
        logger.debug("🛑 Batch processing cancelled")

    def is_processing(self) -> bool:
        """Check if processing is ongoing."""
        return self._processing

    def shutdown(self) -> None:
        """Clean up resources."""
        self.cancel_processing()
        self._executor.shutdown(wait=False)