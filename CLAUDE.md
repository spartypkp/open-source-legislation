# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-source-legislation is a platform for democratizing access to global legislative data. It provides scraped and processed legislation from countries and jurisdictions worldwide in a unified SQL schema format. The project enables developers to build legal applications using primary source legislation data without the typical barriers to accessing this information.

## Architecture

### Core Components

**Scraping Pipeline (3-Phase Architecture):**
1. **Read Phase** (`1_read.py`): Extracts top-level title links from table of contents pages
2. **Scrape Phase** (`2_scrape_regular.py`, `2a_scrape_selenium.py`): Scrapes legislative content using regular HTTP requests or Selenium for complex sites
3. **Process Phase** (`3_process.py`): Processes scraped data, generates embeddings, and establishes node relationships

**Data Models (Pydantic-based):**
- `Node`: Core legislation model with structure/content types
- `NodeID`: Hierarchical identifier system (e.g., `us/ca/statutes/title=1/chapter=2/section=3`)
- `NodeText`: Paragraph-based text content with reference tracking
- `DefinitionHub`: Legal term definitions with scope and inheritance
- `ReferenceHub`: Cross-references between legislation nodes

**Database Schema:**
- PostgreSQL with unified schema across jurisdictions
- Table naming: `{country}_{jurisdiction}_{corpus}` (e.g., `us_ca_statutes`)
- Support for graph traversal and cross-corpus connections

### Directory Structure

```
src/
├── scrapers/
│   ├── {country}/
│   │   ├── {jurisdiction}/
│   │   │   └── {corpus}/
│   │   │       ├── read{STATE}.py
│   │   │       ├── scrape{STATE}.py
│   │   │       └── process{STATE}.py
│   └── 1_SCRAPE_TEMPLATE/  # Template for new scrapers
├── utils/
│   ├── pydanticModels.py   # Core data models
│   ├── scrapingHelpers.py  # Scraping utilities
│   ├── processingHelpers.py # Processing utilities
│   └── utilityFunctions.py # Database and general utilities
└── github/
    └── progressTracker.py  # Track scraper status
```

## Common Development Tasks

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set Python path (adjust path as needed)
export PYTHONPATH=/path/to/open-source-legislation:$PYTHONPATH
```

### Running Scrapers
```bash
# Navigate to specific scraper directory
cd src/scrapers/us/{state}/statutes/

# Run scraping phases in order
python read{STATE}.py    # Extract top-level titles
python scrape{STATE}.py  # Scrape content
python process{STATE}.py # Process and embed data
```

### Database Operations
```bash
# Run SQL file to create corpus tables
psql -U username -d database -f country_jurisdiction_corpus.sql

# Example for Arizona statutes
psql -U myuser -d mydatabase -f us_az_statutes.sql
```

### Creating New Scrapers

1. **Clone Template:**
   ```bash
   cp -r src/1_SCRAPE_TEMPLATE src/scrapers/{country}/{jurisdiction}/{corpus}
   ```

2. **Update Global Variables:**
   - Set `TABLE_NAME` to `{country}_{jurisdiction}_{corpus}`
   - Set `TOC_URL` to table of contents URL
   - Set `BASE_URL` to jurisdiction's base URL

3. **Follow 5-Phase Development Process:**
   - Phase 0: Research legislation structure and HTML
   - Phase 1: Prepare coding environment
   - Phase 2: Implement read functionality
   - Phase 3: Code scraper (Regular/Recursive/Stack methods)
   - Phase 4: Debug and test scraper
   - Phase 5: Process database with embeddings

### Key Utilities

**Database Functions (utilityFunctions.py):**
- `pydantic_insert()`: Insert Pydantic models to database
- `pydantic_select()`: Query database returning Pydantic models
- `regular_select()`: Standard SQL queries

**Scraping Functions (scrapingHelpers.py):**
- `insert_node()`: Insert nodes with duplicate handling
- `get_url_as_soup()`: Fetch URLs as BeautifulSoup with retry logic
- `get_text_clean()`: Clean extracted text content

**Data Models (pydanticModels.py):**
- Use `Node` for all legislation entities
- Use `NodeID.add_level()` to build hierarchical IDs
- Use `NodeText.add_paragraph()` for text content

## Testing and Quality Assurance

- Scrapers should handle reserved/repealed sections
- Test with spot checks across different levels
- Verify node relationships (`parent`, `direct_children`)
- Ensure proper text cleaning and formatting
- Test duplicate handling with version numbers (`-v_2`, `-v_3`)

## Database Connection

Set up PostgreSQL connection and populate database config file as needed for your environment. The system supports both local development and cloud deployment (Supabase).