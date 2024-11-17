import pytest
from datetime import datetime, timedelta
from src.progress import ScanProgress
from unittest.mock import patch

@pytest.fixture
def progress():
    return ScanProgress()

def test_progress_initialization(progress):
    """Test initial state of progress tracker."""
    assert progress.sections_processed == 0
    assert progress.total_links == 0
    assert progress.rate_limit_hits == 0
    assert isinstance(progress.start_time, datetime)

def test_update_section(progress):
    """Test section update tracking."""
    progress.update(section="Benefits")
    assert progress.current_section == "Benefits"
    assert progress.sections_processed == 1

def test_update_links(progress):
    """Test link counting."""
    progress.update(links_found=5)
    progress.update(links_found=3)
    assert progress.total_links == 8

def test_update_depth_distribution(progress):
    """Test depth distribution tracking."""
    progress.update(depth=1)
    progress.update(depth=1)
    progress.update(depth=2)
    assert progress.depth_counts == {"1": 2, "2": 1}

def test_update_content_types(progress):
    """Test content type tracking."""
    progress.update(content_type="guide")
    progress.update(content_type="guide")
    progress.update(content_type="detailed_guide")
    assert progress.content_types == {"guide": 2, "detailed_guide": 1}

def test_rate_limit_tracking(progress):
    """Test rate limit hit tracking."""
    progress.update(rate_limited=True)
    progress.update(rate_limited=True)
    assert progress.rate_limit_hits == 2

def test_get_status(progress):
    """Test status report generation."""
    # Setup some test data
    progress.update(
        section="Benefits",
        links_found=5,
        depth=1,
        content_type="guide",
        rate_limited=True
    )
    
    status = progress.get_status()
    assert status["sections_analyzed"] == 1
    assert status["total_links_found"] == 5
    assert status["rate_limit_hits"] == 1
    assert status["current_section"] == "Benefits"
    assert status["depth_distribution"] == {"1": 1}
    assert status["content_types"] == {"guide": 1}
    assert "scan_duration" in status
    assert "timestamp" in status

@patch('src.progress.logger')
def test_progress_logging(mock_logger, progress):
    """Test progress logging functionality."""
    with patch('src.progress.datetime') as mock_datetime:
        # Setup mock times to trigger logging
        mock_datetime.now.side_effect = [
            datetime(2024, 1, 1, 12, 0, 0),  # start_time
            datetime(2024, 1, 1, 12, 0, 0),  # first update
            datetime(2024, 1, 1, 12, 1, 1),  # second update (>60s later)
        ]
        
        progress.update(section="Benefits")
        progress.update(section="Education")  # Should trigger logging
        
        assert mock_logger.info.call_count >= 2  # Initial section log + progress log