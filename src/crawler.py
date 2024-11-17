import logging
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
from .api_client import GovUKAPIClient, APIError
from .progress import ScanProgress
from .checkpoint import CheckpointManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovUKCrawler:
    """
    Crawler for mapping GOV.UK content structure.
    Implements depth-limited traversal with tracking of visited URLs.
    """
    ROOT_PATH = "/browse"

    def __init__(self, max_depth: int = 5, progress_tracker: Optional[ScanProgress] = None,
                 checkpoint_manager: Optional[CheckpointManager] = None):
        self.api_client = GovUKAPIClient()
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.scan_metadata = {
            "timestamp": datetime.now().isoformat(),
            "depth_limit": max_depth,
            "total_pages": 0,
            "sections_covered": 0,
            "rate_limit_pauses": 0
        }
        self.sections: Dict[str, Any] = {}
        self.progress = progress_tracker or ScanProgress()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

    def _should_process_url(self, url: str) -> bool:
        """
        Determine if a URL should be processed.
        
        Args:
            url: The URL path to check
        
        Returns:
            bool: True if the URL should be processed
        """
        if url in self.visited_urls:
            return False
        if not url.startswith('/'):
            return False
        # Exclude non-content URLs (assets, images, etc.)
        excluded_patterns = ['/assets/', '/images/', '/attachments/']
        return not any(pattern in url for pattern in excluded_patterns)

    def _process_content(self, content: Dict[str, Any], depth: int, section: str) -> None:
        """
        Process a single content item and its related links.
        
        Args:
            content: The content data from the API
            depth: Current depth in the crawl
            section: Current section being processed
        """
        if depth > self.max_depth:
            return

        path = content.get('base_path', '')
        if not path or path in self.visited_urls:
            return

        self.visited_urls.add(path)
        self.scan_metadata["total_pages"] += 1

        # Update progress
        content_type = content.get("document_type", "unknown")
        self.progress.update(
            links_found=1,
            depth=depth,
            content_type=content_type
        )

        # Create page data
        page_data = {
            "path": path,
            "content_type": content_type,
            "last_updated": content.get("updated_at", ""),
            "status": "placeholder" if self.api_client.is_placeholder_content(content) else "active",
            "depth_level": depth,
            "publishing_org": self._extract_publishing_org(content),
            "related_links": []
        }

        # Add page to section
        if section not in self.sections:
            self.sections[section] = {
                "total_pages": 0,
                "active_pages": 0,
                "placeholder_pages": 0,
                "depth_distribution": {},
                "pages": []
            }
            self.scan_metadata["sections_covered"] += 1
            self.progress.update(section=section)

        self.sections[section]["total_pages"] += 1
        if page_data["status"] == "active":
            self.sections[section]["active_pages"] += 1
        else:
            self.sections[section]["placeholder_pages"] += 1

        # Update depth distribution
        depth_str = str(depth)
        if depth_str not in self.sections[section]["depth_distribution"]:
            self.sections[section]["depth_distribution"][depth_str] = 0
        self.sections[section]["depth_distribution"][depth_str] += 1

        # Process related links
        if depth < self.max_depth:
            related_links = self.api_client.get_related_links(content)
            page_data["related_links"] = related_links
            
            for link in related_links:
                if self._should_process_url(link):
                    try:
                        related_content = self.api_client.get_content(link)
                        self._process_content(related_content, depth + 1, section)
                    except APIError as e:
                        logger.warning(f"Failed to fetch related content {link}: {str(e)}")

        self.sections[section]["pages"].append(page_data)

        # Add checkpoint check after processing each page
        if self.checkpoint_manager.should_checkpoint(1):
            state = {
                "scan_metadata": self.scan_metadata,
                "sections": self.sections,
                "visited_urls": list(self.visited_urls),
                "progress": self.progress.get_status()
            }
            self.checkpoint_manager.save_checkpoint(state)

    def _extract_publishing_org(self, content: Dict[str, Any]) -> str:
        """Extract publishing organization from content."""
        try:
            orgs = content.get("links", {}).get("organisations", [])
            return orgs[0].get("title", "") if orgs else ""
        except (IndexError, KeyError):
            return ""

    def crawl_section(self, section_path: str) -> Dict[str, Any]:
        """
        Crawl a specific section of GOV.UK content.
        
        Args:
            section_path: The path to start crawling from
        
        Returns:
            Dict containing the crawl results
        """
        logger.info(f"Starting crawl of section: {section_path}")
        try:
            content = self.api_client.get_content(section_path)
            self._process_content(content, 0, section_path)
        except APIError as e:
            logger.error(f"Failed to crawl section {section_path}: {str(e)}")
            if "Rate limit exceeded" in str(e):
                self.progress.update(rate_limited=True)
            return {}

        return {
            "scan_metadata": self.scan_metadata,
            "sections": self.sections,
            "progress": self.progress.get_status()
        }

    def get_results(self) -> Dict[str, Any]:
        """Get the current crawl results."""
        return {
            "scan_metadata": self.scan_metadata,
            "sections": self.sections
        }

    def get_services_sections(self) -> List[Dict[str, str]]:
        """
        Fetch and parse the main services and information sections.
        
        Returns:
            List of sections with titles and paths.
            Example: [
                {"title": "Benefits", "path": "/browse/benefits"},
                {"title": "Education", "path": "/browse/education"}
            ]
        
        Raises:
            APIError: If unable to fetch or parse the browse page
        """
        try:
            content = self.api_client.get_content(self.ROOT_PATH)
            sections = []
            
            # Extract main sections from the browse page
            if "links" in content:
                for section in content.get("links", {}).get("children", []):
                    if "title" in section and "base_path" in section:
                        sections.append({
                            "title": section["title"],
                            "path": section["base_path"]
                        })
            
            if not sections:
                raise APIError("No sections found in browse page")
                
            return sections
            
        except APIError as e:
            logger.error(f"Failed to fetch services sections: {str(e)}")
            raise

    def analyze_section_depth(self, section: Dict[str, str], max_depth: int = 1) -> Dict:
        """
        Quick analysis of a section to estimate content volume.
        
        Args:
            section: Dictionary containing section title and path
            max_depth: Maximum depth to analyze (default: 1)
            
        Returns:
            Dict containing analysis results:
            {
                "title": str,
                "path": str,
                "estimated_pages": int,
                "subsections": List[str],
                "sample_links": List[str],
                "content_types": Dict[str, int]
            }
        """
        results = {
            "title": section["title"],
            "path": section["path"],
            "estimated_pages": 0,
            "subsections": [],
            "sample_links": [],
            "content_types": {}
        }
        
        try:
            # Get initial section content
            content = self.api_client.get_content(section["path"])
            
            # Extract subsections
            if "links" in content:
                for subsection in content.get("links", {}).get("children", []):
                    if "title" in subsection and "base_path" in subsection:
                        results["subsections"].append(subsection["title"])
                        results["sample_links"].append(subsection["base_path"])
                        
            # Count estimated pages
            results["estimated_pages"] = len(results["sample_links"])
            
            # Record content type if available
            content_type = content.get("document_type", "unknown")
            results["content_types"][content_type] = 1
            
            return results
            
        except APIError as e:
            logger.error(f"Failed to analyze section {section['path']}: {str(e)}")
            return results 

    def restore_from_checkpoint(self, checkpoint_file: str) -> bool:
        """
        Restore crawler state from a checkpoint file.
        
        Args:
            checkpoint_file: Name of the checkpoint file to restore from
            
        Returns:
            bool: True if restoration was successful
        """
        state = self.checkpoint_manager.load_checkpoint(checkpoint_file)
        if not state:
            return False
            
        self.scan_metadata = state.get("scan_metadata", self.scan_metadata)
        self.sections = state.get("sections", {})
        self.visited_urls = set(state.get("visited_urls", []))
        
        # Update progress if available
        if "progress" in state:
            for key, value in state["progress"].items():
                setattr(self.progress, key, value)
                
        return True 