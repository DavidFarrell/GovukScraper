import requests
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from .rate_limiter import RateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API-related errors"""
    pass

class GovUKAPIClient:
    """
    Client for interacting with the GOV.UK Content API.
    Handles rate-limited requests and response parsing.
    """
    def __init__(self, rate_limit: float = 10.0):
        self.base_url = "https://www.gov.uk/api/content"
        self.rate_limiter = RateLimiter(rate_limit)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GOV.UK-Content-Mapper/1.0',
            'Accept': 'application/json'
        })

    def _build_url(self, path: str) -> str:
        """Construct full API URL from path."""
        # Remove leading slash if present to avoid double slashes
        path = path.lstrip('/')
        # Ensure we keep the /content part of the URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and potential errors.
        Raises APIError for non-200 responses.
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Failed to parse JSON response for {response.url}")
            raise APIError("Invalid JSON response from API")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Content not found at {response.url}")
                return {"error": "not_found", "path": response.url}
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise APIError("Rate limit exceeded")
            else:
                logger.error(f"HTTP error occurred: {e}")
                raise APIError(f"HTTP {response.status_code}: {str(e)}")

    @RateLimiter()
    def get_content(self, path: str) -> Dict[str, Any]:
        """
        Fetch content from the GOV.UK Content API.
        
        Args:
            path: The content path (e.g., "/take-pet-abroad")
        
        Returns:
            Dict containing the API response
        
        Raises:
            APIError: If the request fails or returns invalid data
        """
        url = self._build_url(path)
        logger.debug(f"Fetching content from {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out for {url}")
            raise APIError("Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")

    def is_placeholder_content(self, content: Dict[str, Any]) -> bool:
        """
        Check if the content is a placeholder or unmigrated content.
        
        Args:
            content: The API response dictionary
        
        Returns:
            bool: True if content is placeholder/unmigrated
        """
        # Check for common indicators of placeholder content
        if content.get("error") == "not_found":
            return True
        if not content.get("title") or not content.get("body"):
            return True
        if content.get("schema_name") == "placeholder":
            return True
        return False

    @RateLimiter()
    def get_related_links(self, content: Dict[str, Any]) -> List[str]:
        """Extract related content links from content data"""
        links = []
        try:
            # Extract links from content relationships
            for link_type in ["related_items", "related_guides", "related_content"]:
                if link_type in content.get("links", {}):
                    for item in content["links"][link_type]:
                        if "base_path" in item:
                            links.append(item["base_path"])
            return links
        except (KeyError, TypeError):
            return []