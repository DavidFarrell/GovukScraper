import logging
from typing import Dict, Set, Any, Optional, List, Tuple
from queue import PriorityQueue
from datetime import datetime
from pybloom_live import BloomFilter
from .crawler import GovUKCrawler
from .progress import ScanProgress
from .checkpoint import CheckpointManager
import time

logger = logging.getLogger(__name__)

class OptimisedCrawler(GovUKCrawler):
    """
    Optimised version of the GOV.UK crawler with:
    - Bloom filter for efficient URL deduplication
    - Priority queue for important content
    """
    
    def __init__(self, max_depth: int = 5, 
                 progress_tracker: Optional[ScanProgress] = None,
                 checkpoint_manager: Optional[CheckpointManager] = None,
                 max_elements: int = 1_000_000,
                 error_rate: float = 0.1):
        super().__init__(max_depth, progress_tracker, checkpoint_manager)
        self.seen_urls = BloomFilter(capacity=max_elements, error_rate=error_rate)
        self.url_queue: PriorityQueue = PriorityQueue()
        
    def _calculate_priority(self, url: str, content_type: str = None, depth: int = 0) -> int:
        """Calculate priority score for a URL (lower is higher priority)."""
        base_priority = depth * 10  # Deeper pages get lower priority
        
        # Prioritise certain content types
        if content_type:
            priority_types = {
                "guide": -500,  # Much higher priority
                "detailed_guide": -400,
                "service": -300,
                "transaction": -300
            }
            base_priority += priority_types.get(content_type, 0)
            
        # Prioritise certain URL patterns
        if "/services/" in url:
            base_priority -= 100
        if "/guidance/" in url:
            base_priority -= 50
            
        # Add more sophisticated priority calculation
        priority = max(1, base_priority)
        
        # Consider update frequency
        if url in self.update_frequency:
            frequency_score = self.update_frequency[url]
            priority -= frequency_score * 100
            
        # Consider page importance metrics
        if url in self.page_metrics:
            importance_score = self.page_metrics[url].get('importance', 0)
            priority -= importance_score * 50
            
        return max(1, priority)
        
    def add_url_to_queue(self, url: str, content_type: str = None, depth: int = 0) -> None:
        """Add URL to queue with appropriate priority if not seen."""
        if url not in self.seen_urls:
            priority = self._calculate_priority(url, content_type, depth)
            self.url_queue.put((priority, url, depth))
            self.seen_urls.add(url)
            
    def process_batch(self, batch_size: int = 10) -> List[Dict]:
        """Process multiple URLs within rate limits."""
        if self.url_queue.empty():
            return []
            
        results = []
        for _ in range(batch_size):
            if self.url_queue.empty():
                break
            priority, url, depth = self.url_queue.get()
            try:
                content = self.api_client.get_content(url)
                if content:
                    self._process_content(content, depth, self._get_section_for_url(url))
                    results.append(content)
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                
        return results
        
    def _get_section_for_url(self, url: str) -> str:
        """Determine section for URL based on path."""
        parts = url.strip('/').split('/')
        return f"/{parts[0]}" if parts else "/"
        
    def crawl_section(self, section_path: str) -> Dict[str, Any]:
        """Enhanced crawl with batch processing and prioritisation."""
        logger.info(f"Starting optimised crawl of section: {section_path}")
        
        # Add initial URL
        self.add_url_to_queue(section_path, depth=0)
        
        # Process queue in batches
        while not self.url_queue.empty():
            # Run batch processing
            results = self.process_batch()
            
            # Create checkpoint if needed
            if self.checkpoint_manager.should_checkpoint(10):  # Check every 10 pages
                state = {
                    "scan_metadata": self.scan_metadata,
                    "sections": self.sections,
                    "visited_urls": list(self.visited_urls),
                    "progress": self.progress.get_status(),
                    "queue_items": list(self.url_queue.queue)
                }
                self.checkpoint_manager.save_checkpoint(state)
                
        return {
            "scan_metadata": self.scan_metadata,
            "sections": self.sections,
            "progress": self.progress.get_status()
        }
        
    def restore_from_checkpoint(self, checkpoint_file: str) -> bool:
        """Enhanced restore including queue state."""
        state = self.checkpoint_manager.load_checkpoint(checkpoint_file)
        if not state:
            return False
            
        # Restore base state
        success = super().restore_from_checkpoint(checkpoint_file)
        if not success:
            return False
            
        # Restore queue state
        if "queue_items" in state:
            for priority, url, depth in state["queue_items"]:
                self.url_queue.put((priority, url, depth))
                
        return True 
        
    def _manage_memory(self):
        """Implement memory management for long runs"""
        if len(self.visited_urls) > self.max_urls_in_memory:
            # Persist older URLs to disk
            self._persist_urls_to_disk(list(self.visited_urls)[:10000])
            # Clear from memory
            self.visited_urls = set(list(self.visited_urls)[10000:])