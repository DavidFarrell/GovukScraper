from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ScanProgress:
    """
    Tracks progress of GOV.UK content scanning operations.
    Provides real-time metrics and status updates.
    """
    def __init__(self):
        self.start_time = datetime.now()
        self.sections_processed = 0
        self.total_links = 0
        self.current_section = ""
        self.rate_limit_hits = 0
        self.depth_counts = {}
        self.content_types = {}
        self._last_update = datetime.now()
        
    def update(self, **kwargs) -> None:
        """
        Update progress metrics.
        
        Args:
            **kwargs: Supported keys:
                - section: Current section being processed
                - links_found: Number of new links found
                - depth: Current depth level
                - content_type: Type of content found
                - rate_limited: Boolean indicating rate limit hit
        """
        now = datetime.now()
        
        if 'section' in kwargs:
            self.current_section = kwargs['section']
            self.sections_processed += 1
            logger.info(f"Processing section: {self.current_section}")
            
        if 'links_found' in kwargs:
            self.total_links += kwargs['links_found']
            
        if 'depth' in kwargs:
            depth = str(kwargs['depth'])
            self.depth_counts[depth] = self.depth_counts.get(depth, 0) + 1
            
        if 'content_type' in kwargs:
            content_type = kwargs['content_type']
            self.content_types[content_type] = self.content_types.get(content_type, 0) + 1
            
        if kwargs.get('rate_limited', False):
            self.rate_limit_hits += 1
            
        # Log progress every 60 seconds
        if (now - self._last_update).total_seconds() > 60:
            self._log_progress()
            self._last_update = now
    
    def _log_progress(self) -> None:
        """Log current progress metrics."""
        duration = datetime.now() - self.start_time
        logger.info(
            f"Progress: {self.sections_processed} sections, "
            f"{self.total_links} links, "
            f"Duration: {str(duration).split('.')[0]}, "
            f"Rate limits: {self.rate_limit_hits}"
        )
        
    def get_status(self) -> Dict:
        """
        Get current progress status.
        
        Returns:
            Dict containing current progress metrics
        """
        duration = datetime.now() - self.start_time
        return {
            "timestamp": datetime.now().isoformat(),
            "sections_analyzed": self.sections_processed,
            "total_links_found": self.total_links,
            "scan_duration": str(duration).split('.')[0],
            "rate_limit_hits": self.rate_limit_hits,
            "current_section": self.current_section,
            "depth_distribution": self.depth_counts,
            "content_types": self.content_types
        } 