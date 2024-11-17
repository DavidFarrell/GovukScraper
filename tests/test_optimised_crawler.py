import pytest
from unittest.mock import Mock, patch
from src.optimised_crawler import OptimisedCrawler
from src.progress import ScanProgress
from src.checkpoint import CheckpointManager

@pytest.fixture
def optimised_crawler(tmp_path):
    """Provide configured OptimisedCrawler instance."""
    progress = ScanProgress()
    checkpoint_manager = CheckpointManager(str(tmp_path / "checkpoints"))
    return OptimisedCrawler(
        max_depth=2,
        progress_tracker=progress,
        checkpoint_manager=checkpoint_manager
    )

def test_url_deduplication(optimised_crawler):
    """Test Bloom filter URL deduplication."""
    url = "/test/page"
    
    # First addition should work
    optimised_crawler.add_url_to_queue(url)
    assert not optimised_crawler.url_queue.empty()
    
    # Second addition should be blocked
    optimised_crawler.add_url_to_queue(url)
    assert optimised_crawler.url_queue.qsize() == 1

def test_checkpoint_restoration(optimised_crawler):
    """Test queue state restoration from checkpoint."""
    # Create a test state
    test_state = {
        "queue_items": [
            (1, "/test/page1", 0),
            (2, "/test/page2", 1)
        ]
    }
    
    # Save and restore
    checkpoint_file = optimised_crawler.checkpoint_manager.save_checkpoint(test_state)
    success = optimised_crawler.restore_from_checkpoint(checkpoint_file)
    
    assert success
    assert optimised_crawler.url_queue.qsize() == 2

def test_section_path_extraction(optimised_crawler):
    """Test section path extraction from URLs."""
    assert optimised_crawler._get_section_for_url("/benefits/universal-credit") == "/benefits"
    assert optimised_crawler._get_section_for_url("/") == "/"