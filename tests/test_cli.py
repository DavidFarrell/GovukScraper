import pytest
import click
from click.testing import CliRunner
from pathlib import Path
import json
from unittest.mock import patch, Mock
from src.cli import main, parse_sections_input, save_json_output, save_csv_output, save_report_output
from src.optimised_crawler import OptimisedCrawler
from datetime import datetime
from src.api_client import APIError

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_sections():
    return [
        {"title": "Benefits", "path": "/browse/benefits"},
        {"title": "Education", "path": "/browse/education"}
    ]

def test_parse_sections_input_empty():
    """Test parsing empty sections input."""
    available = [{"title": "Test", "path": "/test"}]
    result = parse_sections_input(None, available)
    assert result == available

def test_parse_sections_input_valid():
    """Test parsing valid sections input."""
    available = [
        {"title": "Benefits", "path": "/browse/benefits"},
        {"title": "Education", "path": "/browse/education"}
    ]
    result = parse_sections_input("Benefits,Education", available)
    assert len(result) == 2
    assert result[0]["title"] == "Benefits"

def test_parse_sections_input_invalid():
    """Test parsing invalid sections input."""
    available = [{"title": "Test", "path": "/test"}]
    with pytest.raises(click.BadParameter):
        parse_sections_input("NonExistent", available)

def test_save_json_output(tmp_path):
    """Test JSON output saving."""
    data = {"test": "data"}
    output_path = tmp_path / "test.json"
    save_json_output(data, output_path)
    
    with open(output_path) as f:
        saved_data = json.load(f)
    assert saved_data == data

def test_save_csv_output(tmp_path):
    """Test CSV output saving."""
    data = {
        "sections": {
            "test_section": {
                "pages": [
                    {
                        "path": "/test",
                        "content_type": "guide",
                        "status": "active",
                        "depth_level": 1,
                        "publishing_org": "Test Org",
                        "last_updated": "2024-01-01",
                        "related_links": []
                    }
                ]
            }
        }
    }
    output_path = tmp_path / "test.csv"
    save_csv_output(data, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        header = f.readline().strip()
        assert "section,path,content_type" in header

def test_save_report_output(tmp_path):
    """Test report output saving."""
    data = {
        "progress": {
            "sections_analyzed": 1,
            "total_links_found": 10,
            "rate_limit_hits": 0,
            "scan_duration": "00:01:00",
            "content_types": {"guide": 5, "detailed_guide": 5}
        }
    }
    output_path = tmp_path / "test.report"
    save_report_output(data, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        content = f.read()
        assert "GOV.UK Content Mapping Report" in content
        assert "Sections analyzed: 1" in content

def test_save_report_output_detailed(tmp_path):
    """Test detailed report generation."""
    data = {
        "progress": {
            "sections_analyzed": 5,
            "total_links_found": 100,
            "rate_limit_hits": 2,
            "scan_duration": "01:30:00",
            "content_types": {
                "guide": 50,
                "detailed_guide": 30,
                "manual": 20
            }
        },
        "analysis": {
            "section1": {
                "update_patterns": {
                    "newest_update": "2024-01-01",
                    "oldest_update": "2023-01-01"
                }
            }
        }
    }
    
    output_path = tmp_path / "test.report"
    save_report_output(data, output_path)
    
    with open(output_path) as f:
        content = f.read()
        assert "GOV.UK Content Mapping Report" in content
        assert "Content Types" in content
        assert "guide: 50" in content 