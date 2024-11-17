import pytest
import responses
from src.api_client import GovUKAPIClient, APIError

@pytest.fixture
def api_client():
    return GovUKAPIClient()

@responses.activate
def test_get_content_success(api_client):
    """Test successful API content retrieval."""
    test_path = "/test-path"
    mock_response = {
        "base_path": test_path,
        "title": "Test Content",
        "body": "Test body content",
        "links": {
            "organisations": [
                {"title": "Test Org"}
            ]
        }
    }
    
    responses.add(
        responses.GET,
        f"{api_client.base_url}{test_path}",
        json=mock_response,
        status=200
    )
    
    content = api_client.get_content(test_path)
    assert content["base_path"] == test_path
    assert content["title"] == "Test Content"

@responses.activate
def test_get_content_404(api_client):
    """Test 404 response handling."""
    test_path = "/nonexistent"
    
    responses.add(
        responses.GET,
        f"{api_client.base_url}{test_path}",
        status=404
    )
    
    content = api_client.get_content(test_path)
    assert content["error"] == "not_found"

@responses.activate
def test_get_content_rate_limit(api_client):
    """Test rate limit response handling."""
    test_path = "/test-path"
    
    responses.add(
        responses.GET,
        f"{api_client.base_url}{test_path}",
        status=429
    )
    
    with pytest.raises(APIError, match="Rate limit exceeded"):
        api_client.get_content(test_path)

def test_is_placeholder_content(api_client):
    """Test placeholder content detection."""
    # Test empty content
    assert api_client.is_placeholder_content({}) == True
    
    # Test normal content
    normal_content = {
        "title": "Test",
        "body": "Content",
        "schema_name": "detailed_guide"
    }
    assert api_client.is_placeholder_content(normal_content) == False
    
    # Test placeholder content
    placeholder_content = {
        "schema_name": "placeholder",
        "title": "Test"
    }
    assert api_client.is_placeholder_content(placeholder_content) == True

def test_get_related_links(api_client):
    """Test related links extraction."""
    content = {
        "links": {
            "related": [
                {"base_path": "/link1"},
                {"base_path": "/link2"}
            ],
            "organisations": [
                {"base_path": "/org1"}
            ]
        }
    }
    
    links = api_client.get_related_links(content)
    assert len(links) == 3
    assert "/link1" in links
    assert "/link2" in links
    assert "/org1" in links 