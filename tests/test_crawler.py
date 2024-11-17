import pytest
import responses
from src.crawler import GovUKCrawler
from src.api_client import APIError
from src.progress import ScanProgress
from src.checkpoint import CheckpointManager

@pytest.fixture
def crawler():
    """Fixture to provide a configured crawler instance."""
    return GovUKCrawler(max_depth=2)

@pytest.fixture
def progress_tracker():
    return ScanProgress()

@pytest.fixture
def checkpoint_manager(tmp_path):
    """Provide configured CheckpointManager instance."""
    return CheckpointManager(str(tmp_path / "checkpoints"))

@pytest.fixture
def crawler_with_checkpoint(checkpoint_manager):
    """Provide crawler with checkpoint manager."""
    return GovUKCrawler(max_depth=2, checkpoint_manager=checkpoint_manager)

def test_should_process_url(crawler):
    """Test URL processing logic."""
    # Valid URLs
    assert crawler._should_process_url("/valid/path") == True
    assert crawler._should_process_url("/another/valid/path") == True
    
    # Invalid URLs
    assert crawler._should_process_url("/assets/image.jpg") == False
    assert crawler._should_process_url("/images/photo.png") == False
    assert crawler._should_process_url("http://external.com") == False
    
    # Already visited URLs
    crawler.visited_urls.add("/visited/path")
    assert crawler._should_process_url("/visited/path") == False 

@responses.activate
def test_get_services_sections(crawler):
    """Test fetching main services sections."""
    mock_browse_response = {
        "base_path": "/browse",
        "links": {
            "children": [
                {
                    "title": "Benefits",
                    "base_path": "/browse/benefits"
                },
                {
                    "title": "Education",
                    "base_path": "/browse/education"
                }
            ]
        }
    }
    
    responses.add(
        responses.GET,
        f"{crawler.api_client.base_url}/browse",
        json=mock_browse_response,
        status=200
    )
    
    sections = crawler.get_services_sections()
    assert len(sections) == 2
    assert sections[0]["title"] == "Benefits"
    assert sections[0]["path"] == "/browse/benefits"
    assert sections[1]["title"] == "Education"
    assert sections[1]["path"] == "/browse/education"

@responses.activate
def test_get_services_sections_empty():
    """Test handling of empty browse page."""
    crawler = GovUKCrawler()
    mock_response = {
        "base_path": "/browse",
        "links": {}
    }
    
    responses.add(
        responses.GET,
        f"{crawler.api_client.base_url}/browse",
        json=mock_response,
        status=200
    )
    
    with pytest.raises(APIError, match="No sections found in browse page"):
        crawler.get_services_sections()

@responses.activate
def test_analyze_section_depth(crawler):
    """Test section analysis functionality."""
    section = {
        "title": "Benefits",
        "path": "/browse/benefits"
    }
    
    mock_section_response = {
        "base_path": "/browse/benefits",
        "document_type": "browse_page",
        "links": {
            "children": [
                {
                    "title": "Universal Credit",
                    "base_path": "/browse/benefits/universal-credit"
                },
                {
                    "title": "Disability benefits",
                    "base_path": "/browse/benefits/disability"
                }
            ]
        }
    }
    
    responses.add(
        responses.GET,
        f"{crawler.api_client.base_url}/browse/benefits",
        json=mock_section_response,
        status=200
    )
    
    analysis = crawler.analyze_section_depth(section)
    assert analysis["title"] == "Benefits"
    assert analysis["path"] == "/browse/benefits"
    assert analysis["estimated_pages"] == 2
    assert len(analysis["subsections"]) == 2
    assert "Universal Credit" in analysis["subsections"]
    assert "browse_page" in analysis["content_types"]

@responses.activate
def test_crawler_with_progress_tracking(crawler, progress_tracker):
    """Test crawler integration with progress tracking."""
    crawler.progress = progress_tracker
    
    section = {
        "title": "Test Section",
        "path": "/browse/test"
    }
    
    mock_content = {
        "base_path": "/browse/test",
        "document_type": "guide",
        "links": {
            "children": [
                {
                    "title": "Subsection 1",
                    "base_path": "/browse/test/sub1"
                }
            ]
        }
    }
    
    responses.add(
        responses.GET,
        f"{crawler.api_client.base_url}/browse/test",
        json=mock_content,
        status=200
    )
    
    # Mock subsection content
    responses.add(
        responses.GET,
        f"{crawler.api_client.base_url}/browse/test/sub1",
        json={"base_path": "/browse/test/sub1", "document_type": "guide"},
        status=200
    )
    
    crawler.crawl_section(section["path"])
    
    status = progress_tracker.get_status()
    assert status["sections_analyzed"] >= 1
    assert status["total_links_found"] >= 1
    assert "guide" in status["content_types"]
    assert status["current_section"] == "/browse/test"

@responses.activate
def test_crawler_checkpoint_creation(crawler_with_checkpoint):
    """Test checkpoint creation during crawl."""
    # Mock the content response
    mock_content = {
        "base_path": "/test",
        "document_type": "guide",
        "links": {
            "children": [{"base_path": f"/test/child{i}"} for i in range(150)]  # Enough to trigger checkpoint
        }
    }
    
    # Add main response
    responses.add(
        responses.GET,
        f"{crawler_with_checkpoint.api_client.base_url}/test",
        json=mock_content,
        status=200
    )
    
    # Add responses for child pages
    for i in range(150):
        responses.add(
            responses.GET,
            f"{crawler_with_checkpoint.api_client.base_url}/test/child{i}",
            json={"base_path": f"/test/child{i}", "document_type": "guide"},
            status=200
        )
    
    # Crawl should create at least one checkpoint
    crawler_with_checkpoint.crawl_section("/test")
    
    # Check if checkpoint was created
    checkpoints = list(crawler_with_checkpoint.checkpoint_manager.checkpoint_dir.glob("checkpoint_*.json"))
    assert len(checkpoints) > 0

@responses.activate
def test_crawler_restore_from_checkpoint(crawler_with_checkpoint, checkpoint_manager):
    """Test restoring crawler state from checkpoint."""
    # Create a checkpoint with known state
    test_state = {
        "scan_metadata": {
            "total_pages": 50,
            "sections_covered": 1
        },
        "sections": {
            "/test": {
                "pages": [{"path": "/test/page1"}]
            }
        },
        "visited_urls": ["/test/page1"],
        "progress": {
            "total_links": 50,
            "sections_processed": 1
        }
    }
    
    checkpoint_file = checkpoint_manager.save_checkpoint(test_state)
    
    # Create new crawler and restore from checkpoint
    new_crawler = GovUKCrawler(checkpoint_manager=checkpoint_manager)
    success = new_crawler.restore_from_checkpoint(checkpoint_file)
    
    assert success
    assert new_crawler.scan_metadata["total_pages"] == 50
    assert "/test/page1" in new_crawler.visited_urls
    assert "/test" in new_crawler.sections

@responses.activate
def test_crawler_checkpoint_interval(crawler_with_checkpoint):
    """Test checkpoint creation at correct intervals."""
    mock_content = {
        "base_path": "/test",
        "document_type": "guide",
        "links": {
            "children": [{"base_path": f"/test/page{i}"} for i in range(50)]
        }
    }
    
    responses.add(
        responses.GET,
        f"{crawler_with_checkpoint.api_client.base_url}/test",
        json=mock_content,
        status=200
    )
    
    # Set a smaller checkpoint interval for testing
    crawler_with_checkpoint.checkpoint_manager.checkpoint_interval = 25
    
    # Add responses for child pages
    for i in range(50):
        responses.add(
            responses.GET,
            f"{crawler_with_checkpoint.api_client.base_url}/test/page{i}",
            json={"base_path": f"/test/page{i}", "document_type": "guide"},
            status=200
        )
    
    crawler_with_checkpoint.crawl_section("/test")
    
    # Should have created at least 2 checkpoints (50 pages / 25 interval)
    checkpoints = list(crawler_with_checkpoint.checkpoint_manager.checkpoint_dir.glob("checkpoint_*.json"))
    assert len(checkpoints) >= 2