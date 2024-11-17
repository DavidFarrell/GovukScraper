import logging
from typing import Dict, List
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class ContentAnalyser:
    """
    Analyses patterns and trends in GOV.UK content structure.
    Provides insights into content organisation and relationships.
    """
    
    def analyse_section_trends(self, section_data: Dict) -> Dict:
        """
        Analyse patterns in section content:
        - Update frequency
        - Content type distribution
        - Link depth patterns
        - Common organisations
        
        Args:
            section_data: Dictionary containing section content data
            
        Returns:
            Dict containing analysis results
        """
        return {
            "update_patterns": self._analyse_update_patterns(section_data),
            "content_distribution": self._analyse_content_types(section_data),
            "depth_metrics": self._analyse_depth_patterns(section_data),
            "org_relationships": self._analyse_organisations(section_data)
        }
        
    def _analyse_update_patterns(self, section_data: Dict) -> Dict:
        """Analyse content update frequency and patterns."""
        updates = []
        for page in section_data.get("pages", []):
            if "last_updated" in page:
                try:
                    update_time = datetime.fromisoformat(page["last_updated"])
                    updates.append(update_time)
                except ValueError:
                    continue
                    
        if not updates:
            return {"error": "No update data available"}
            
        updates.sort()
        average_timestamp = float(sum(dt.timestamp() for dt in updates)) / len(updates)
        average_dt = datetime.fromtimestamp(average_timestamp)
        
        return {
            "oldest_update": updates[0].isoformat(),
            "newest_update": updates[-1].isoformat(),
            "total_updates": len(updates),
            "average_age_days": float((datetime.now() - average_dt).days)
        }
        
    def _analyse_content_types(self, section_data: Dict) -> Dict:
        """Analyse distribution of content types."""
        content_types = Counter()
        for page in section_data.get("pages", []):
            content_types[page.get("content_type", "unknown")] += 1
            
        return {
            "type_distribution": dict(content_types),
            "most_common": content_types.most_common(3),
            "total_types": len(content_types)
        }
        
    def _analyse_depth_patterns(self, section_data: Dict) -> Dict:
        """Analyse content depth and navigation patterns."""
        depth_counts = Counter()
        max_depth = 0
        total_pages = 0
        
        for page in section_data.get("pages", []):
            depth = page.get("depth_level", 0)
            depth_counts[depth] += 1
            max_depth = max(max_depth, depth)
            total_pages += 1
            
        return {
            "depth_distribution": dict(depth_counts),
            "max_depth": max_depth,
            "average_depth": sum(d * c for d, c in depth_counts.items()) / total_pages if total_pages else 0
        }
        
    def _analyse_organisations(self, section_data: Dict) -> Dict:
        """Analyse organisational relationships and ownership."""
        orgs = Counter()
        for page in section_data.get("pages", []):
            org = page.get("publishing_org", "")
            if org:
                orgs[org] += 1
                
        return {
            "org_distribution": dict(orgs),
            "primary_publishers": orgs.most_common(5),
            "total_organisations": len(orgs)
        }
        
    def generate_section_report(self, section_data: Dict) -> Dict:
        """
        Generate detailed section report including:
        - Content freshness
        - Navigation complexity
        - Related content mapping
        - Organisation ownership
        
        Args:
            section_data: Dictionary containing section content
            
        Returns:
            Dict containing comprehensive analysis
        """
        trends = self.analyse_section_trends(section_data)
        
        return {
            "section_title": section_data.get("title", "Unknown Section"),
            "analysis_timestamp": datetime.now().isoformat(),
            "content_freshness": {
                "update_patterns": trends["update_patterns"],
                "staleness_score": self._calculate_staleness_score(trends["update_patterns"])
            },
            "navigation_metrics": {
                "depth_patterns": trends["depth_metrics"],
                "complexity_score": self._calculate_complexity_score(trends["depth_metrics"])
            },
            "content_ownership": {
                "organisations": trends["org_relationships"],
                "primary_owner": trends["org_relationships"]["primary_publishers"][0] if trends["org_relationships"]["primary_publishers"] else None
            },
            "type_analysis": trends["content_distribution"]
        }
        
    def _calculate_staleness_score(self, update_data: Dict) -> float:
        """Calculate content staleness score (0-1, where 1 is most stale)."""
        if "error" in update_data:
            return 1.0
            
        try:
            newest_update = datetime.fromisoformat(update_data["newest_update"])
            age_days = (datetime.now() - newest_update).days
            return min(1.0, age_days / 365)  # Scale to 1 year
        except (KeyError, ValueError):
            return 1.0
            
    def _calculate_complexity_score(self, depth_data: Dict) -> float:
        """Calculate navigation complexity score (0-1, where 1 is most complex)."""
        max_depth = depth_data.get("max_depth", 0)
        avg_depth = depth_data.get("average_depth", 0)
        
        # Consider both maximum depth and average depth
        depth_score = min(1.0, max_depth / 10)  # Scale to 10 levels
        avg_score = min(1.0, avg_depth / 5)     # Scale to 5 levels
        
        return (depth_score + avg_score) / 2 