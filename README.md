# GOV.UK Content Mapping Tool

A Python-based crawler that maps the structure and metadata of www.gov.uk content through their Content API.

## Installation

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python -m src.cli --depth=5 --output-format=json
```

## Features

- Rate-limited crawling (10 requests/second)
- Depth-limited traversal
- Multiple output formats (JSON, CSV)
- Progress tracking 