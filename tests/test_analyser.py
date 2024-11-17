import pytest
from datetime import datetime, timedelta
from src.analyser import ContentAnalyser

@pytest.fixture
def analyser():
    """Provide configured ContentAnalyser instance."""
    return ContentAnalyser()

@pytest.fixture
def sample_section_data():
    """Provide sample section data for testing."""
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)
    
    return {
        "title": "Test Section",
        "pages": [
            {
                "path": "/test/page1",
                "content_type": "guide",
                "last_updated": now.isoformat(),
                "depth_level": 1,
                "publishing_org": "Department A",
                "status": "active"
            },
            {
                "path": "/test/page2",
                "content_type": "guide",
                "last_updated": yesterday.isoformat(),
                "depth_level": 2,
                "publishing_org": "Department A",
                "status": "active"
            },
            {
                "path": "/test/page3",
                "content_type": "detailed_guide",
                "last_updated": last_week.isoformat(),
                "depth_level": 2,
                "publishing_org": "Department B",
                "status": "active"
            }
        ]
    }

def test_analyse_update_patterns(analyser, sample_section_data):
    """Test analysis of content update patterns."""
    patterns = analyser._analyse_update_patterns(sample_section_data)
    
    assert "oldest_update" in patterns
    assert "newest_update" in patterns
    assert patterns["total_updates"] == 3
    assert isinstance(patterns["average_age_days"], float)
    assert patterns["average_age_days"] >= 0

def test_analyse_content_types(analyser, sample_section_data):
    """Test analysis of content type distribution."""
    distribution = analyser._analyse_content_types(sample_section_data)
    
    assert distribution["type_distribution"]["guide"] == 2
    assert distribution["type_distribution"]["detailed_guide"] == 1
    assert distribution["total_types"] == 2
    assert len(distribution["most_common"]) <= 3

def test_analyse_depth_patterns(analyser, sample_section_data):
    """Test analysis of content depth patterns."""
    patterns = analyser._analyse_depth_patterns(sample_section_data)
    
    assert patterns["max_depth"] == 2
    assert patterns["depth_distribution"] == {1: 1, 2: 2}
    assert patterns["average_depth"] == 5/3  # (1 + 2 + 2) / 3

def test_analyse_organisations(analyser, sample_section_data):
    """Test analysis of organisational relationships."""
    org_analysis = analyser._analyse_organisations(sample_section_data)
    
    assert org_analysis["total_organisations"] == 2
    assert org_analysis["org_distribution"]["Department A"] == 2
    assert org_analysis["org_distribution"]["Department B"] == 1
    assert org_analysis["primary_publishers"][0][0] == "Department A"

def test_generate_section_report(analyser, sample_section_data):
    """Test generation of comprehensive section report."""
    report = analyser.generate_section_report(sample_section_data)
    
    assert "section_title" in report
    assert "analysis_timestamp" in report
    assert "content_freshness" in report
    assert "navigation_metrics" in report
    assert "content_ownership" in report
    assert "type_analysis" in report
    assert isinstance(report["content_freshness"]["staleness_score"], float)
    assert isinstance(report["navigation_metrics"]["complexity_score"], float)

def test_analyse_empty_section(analyser):
    """Test handling of empty section data."""
    empty_section = {"title": "Empty", "pages": []}
    
    trends = analyser.analyse_section_trends(empty_section)
    assert "error" in trends["update_patterns"]
    assert trends["content_distribution"]["total_types"] == 0
    assert trends["depth_metrics"]["max_depth"] == 0
    assert trends["org_relationships"]["total_organisations"] == 0

def test_staleness_score_calculation(analyser):
    """Test calculation of content staleness score."""
    update_data = {
        "newest_update": datetime.now().isoformat()
    }
    score = analyser._calculate_staleness_score(update_data)
    assert 0 <= score <= 1

def test_complexity_score_calculation(analyser):
    """Test calculation of navigation complexity score."""
    depth_data = {
        "max_depth": 5,
        "average_depth": 2.5
    }
    score = analyser._calculate_complexity_score(depth_data)
    assert 0 <= score <= 1 