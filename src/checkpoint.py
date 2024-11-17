import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CheckpointManager:
    """Manages crawler state checkpoints for recovery and resumption."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_interval = 100  # Save every 100 pages
        self.pages_since_checkpoint = 0
        self.checkpoint_dir.mkdir(exist_ok=True)
        
    def save_checkpoint(self, state: Dict) -> str:
        """
        Save current crawler state to checkpoint file.
        
        Args:
            state: Dictionary containing crawler state including:
                - visited_urls
                - sections data
                - progress metrics
                - scan metadata
        
        Returns:
            str: Checkpoint filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{timestamp}.json"
        filepath = self.checkpoint_dir / filename
        
        checkpoint_data = {
            "timestamp": timestamp,
            "state": state,
            "metadata": {
                "pages_processed": state.get("scan_metadata", {}).get("total_pages", 0),
                "sections_covered": state.get("scan_metadata", {}).get("sections_covered", 0)
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Checkpoint saved: {filename}")
            self.pages_since_checkpoint = 0
            return filename
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {str(e)}")
            raise
            
    def load_checkpoint(self, filename: str) -> Optional[Dict]:
        """
        Restore crawler state from checkpoint file.
        
        Args:
            filename: Name of checkpoint file to load
            
        Returns:
            Dict containing crawler state or None if file not found
        """
        filepath = self.checkpoint_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Checkpoint file not found: {filename}")
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            logger.info(f"Checkpoint loaded: {filename}")
            return checkpoint_data.get("state")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {str(e)}")
            return None
            
    def clean_old_checkpoints(self, max_age_hours: int = 24) -> None:
        """
        Remove checkpoints older than specified age.
        
        Args:
            max_age_hours: Maximum age of checkpoints in hours
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                # Extract timestamp from filename
                timestamp_str = checkpoint_file.stem.split('_', 1)[1]  # Split only on first underscore
                checkpoint_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if checkpoint_time < cutoff_time:
                    checkpoint_file.unlink()
                    logger.info(f"Removed old checkpoint: {checkpoint_file.name}")
            except Exception as e:
                logger.warning(f"Failed to process checkpoint file {checkpoint_file.name}: {str(e)}")
                
    def should_checkpoint(self, pages_processed: int) -> bool:
        """
        Determine if it's time to create a new checkpoint.
        
        Args:
            pages_processed: Number of pages processed since last checkpoint
            
        Returns:
            bool: True if checkpoint should be created
        """
        self.pages_since_checkpoint += pages_processed
        if self.pages_since_checkpoint >= self.checkpoint_interval:
            self.pages_since_checkpoint = 0  # Reset counter when threshold is reached
            return True
        return False