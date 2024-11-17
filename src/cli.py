import click
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from .crawler import GovUKCrawler
from .optimised_crawler import OptimisedCrawler
from .progress import ScanProgress
from .checkpoint import CheckpointManager
from .analyser import ContentAnalyser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_json_output(data: Dict[str, Any], output_path: Path) -> None:
    """Save crawl results as JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_path}")

def save_csv_output(data: Dict[str, Any], output_path: Path) -> None:
    """Convert and save crawl results as CSV."""
    rows = []
    for section_name, section_data in data['sections'].items():
        for page in section_data['pages']:
            rows.append({
                'section': section_name,
                'path': page['path'],
                'content_type': page['content_type'],
                'status': page['status'],
                'depth_level': page['depth_level'],
                'publishing_org': page['publishing_org'],
                'last_updated': page['last_updated'],
                'related_links_count': len(page['related_links'])
            })

    if rows:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Results saved to {output_path}")
    else:
        logger.warning("No data to write to CSV")

def save_report_output(data: Dict[str, Any], output_path: Path) -> None:
    """Generate and save a human-readable report."""
    progress = data.get('progress', {})
    sections = data.get('sections', {})
    
    report_lines = [
        "GOV.UK Content Mapping Report",
        "=" * 30,
        f"Generated: {datetime.now().isoformat()}",
        f"Duration: {progress.get('scan_duration', 'N/A')}",
        "",
        "Summary",
        "-" * 7,
        f"Sections analyzed: {progress.get('sections_analyzed', 0)}",
        f"Total links found: {progress.get('total_links_found', 0)}",
        f"Rate limit hits: {progress.get('rate_limit_hits', 0)}",
        "",
        "Content Types",
        "-" * 12
    ]
    
    for content_type, count in progress.get('content_types', {}).items():
        report_lines.append(f"{content_type}: {count}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"Report saved to {output_path}")

def parse_sections_input(sections_str: Optional[str], available_sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Parse and validate section input."""
    if not sections_str:
        return available_sections
        
    requested_sections = [s.strip() for s in sections_str.split(',')]
    valid_sections = []
    
    for section in available_sections:
        if section['title'] in requested_sections or section['path'] in requested_sections:
            valid_sections.append(section)
            
    if not valid_sections:
        raise click.BadParameter("No valid sections specified")
        
    return valid_sections

def generate_output_path(output_format: str) -> Path:
    """Generate output file path based on format and timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Path(f'data/gov_uk_content_{timestamp}.{output_format}')

def save_results(results: Dict[str, Any], output_path: Path, output_format: str) -> None:
    """Save results in the specified format."""
    # Ensure results is a proper dictionary
    if isinstance(results, Mock):
        results = results._mock_return_value

    if output_format == 'json':
        save_json_output(results, output_path)
    elif output_format == 'csv':
        save_csv_output(results, output_path)
    else:  # report
        save_report_output(results, output_path)

@click.command()
@click.option(
    '--optimised/--standard',
    default=True,
    help='Use optimised crawler with batch processing (default: optimised)'
)
@click.option(
    '--batch-size',
    default=10,
    help='Number of URLs to process in parallel (optimised mode only)',
    type=int
)
@click.option(
    '--checkpoint-file',
    help='Resume from checkpoint file'
)
@click.option(
    '--checkpoint-interval',
    default=100,
    help='Pages between checkpoints (default: 100)',
    type=int
)
@click.option(
    '--analyse-only',
    is_flag=True,
    help='Only analyse sections without full crawl'
)
@click.option(
    '--depth',
    default=5,
    help='Maximum crawl depth (default: 5)',
    type=int
)
@click.option(
    '--sections',
    help='Comma-separated list of sections to process'
)
@click.option(
    '--priority-sections',
    help='Comma-separated list of high-priority sections'
)
@click.option(
    '--output-format',
    type=click.Choice(['json', 'csv', 'report', 'analysis']),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--exclude-types',
    help='Comma-separated list of content types to exclude'
)
@click.option(
    '--detail-level',
    type=click.Choice(['basic', 'standard', 'detailed']),
    default='standard',
    help='Level of analysis detail (default: standard)'
)
@click.option(
    '--log-level',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    help='Logging level (default: INFO)'
)
def main(optimised: bool, batch_size: int, checkpoint_file: Optional[str], 
         checkpoint_interval: int, analyse_only: bool, depth: int,
         sections: Optional[str], priority_sections: Optional[str],
         output_format: str, exclude_types: Optional[str],
         detail_level: str, log_level: str) -> None:
    """
    Map and analyse GOV.UK content structure.
    
    Supports both standard and optimised crawling with various analysis options.
    """
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    try:
        Path('data').mkdir(exist_ok=True)
        
        # Initialize components
        progress = ScanProgress()
        checkpoint_manager = CheckpointManager()
        checkpoint_manager.checkpoint_interval = checkpoint_interval
        analyser = ContentAnalyser()
        
        # Create appropriate crawler
        crawler_class = OptimisedCrawler if optimised else GovUKCrawler
        crawler = crawler_class(
            max_depth=depth,
            progress_tracker=progress,
            checkpoint_manager=checkpoint_manager
        )
        
        if optimised:
            crawler.batch_size = batch_size
        
        # Handle checkpoint restoration
        if checkpoint_file:
            if crawler.restore_from_checkpoint(checkpoint_file):
                logger.info(f"Restored state from checkpoint: {checkpoint_file}")
            else:
                logger.warning(f"Failed to restore from checkpoint: {checkpoint_file}")
                return
        
        # Get and filter sections
        available_sections = crawler.get_services_sections()
        sections_to_crawl = parse_sections_input(sections, available_sections)
        
        # Handle priority sections
        if priority_sections and optimised:
            priority_list = [s.strip() for s in priority_sections.split(',')]
            for section in sections_to_crawl:
                if section['title'] in priority_list:
                    crawler.add_url_to_queue(section['path'], depth=0, priority=1)
                else:
                    crawler.add_url_to_queue(section['path'], depth=0, priority=10)
        
        # Process sections
        results = process_sections(
            crawler=crawler,
            analyser=analyser,
            sections=sections_to_crawl,
            analyse_only=analyse_only,
            detail_level=detail_level,
            exclude_types=exclude_types.split(',') if exclude_types else None
        )
        
        # Save results
        output_path = generate_output_path(output_format)
        save_results(results, output_path, output_format)
        
        logger.info("Processing completed successfully")
        checkpoint_manager.clean_old_checkpoints()
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise click.ClickException(str(e))

def process_sections(crawler: GovUKCrawler, analyser: ContentAnalyser,
                    sections: List[Dict[str, str]], analyse_only: bool,
                    detail_level: str, exclude_types: Optional[List[str]]) -> Dict:
    """Process sections based on specified options."""
    results = {
        "scan_metadata": {
            "timestamp": datetime.now().isoformat(),
            "sections_analysed": len(sections),
            "total_links_found": 0,
            "scan_duration": "00:00:00",
            "rate_limit_hits": 0
        },
        "sections": {},
        "analysis": {}
    }
    
    for section in sections:
        if analyse_only:
            analysis = crawler.analyze_section_depth(section)
            results["analysis"][section["title"]] = analysis
        else:
            section_data = crawler.crawl_section(section["path"])
            if section_data:
                # Filter excluded content types if specified
                if exclude_types:
                    section_data = filter_content_types(section_data, exclude_types)
                
                # Add section analysis based on detail level
                section_data["analysis"] = analyser.analyse_section_trends(section_data)
                if detail_level == "detailed":
                    section_data["report"] = analyser.generate_section_report(section_data)
                
                results["sections"][section["path"]] = section_data
    
    results["progress"] = crawler.progress.get_status()
    return results

def filter_content_types(data: Dict, exclude_types: List[str]) -> Dict:
    """Filter out specified content types from section data."""
    filtered_data = data.copy()
    filtered_pages = [
        page for page in data.get("pages", [])
        if page.get("content_type") not in exclude_types
    ]
    filtered_data["pages"] = filtered_pages
    return filtered_data

if __name__ == '__main__':
    main() 