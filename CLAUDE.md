# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-source-legislation is a platform for democratizing access to global legislative data. It provides scraped and processed legislation from countries and jurisdictions worldwide in a unified SQL schema format. The project enables developers to build legal applications using primary source legislation data without the typical barriers to accessing this information.

**Key Features:**
- Unified PostgreSQL schema with pgvector support for embeddings
- Hierarchical node-based legislation modeling
- Cross-corpus and cross-jurisdiction reference tracking
- Pydantic-based data models for validation and type safety
- LLM-ready with pre-generated embeddings
- 50+ US state and federal legislation corpora (various stages of completion)
- Python SDK with Instructor library integration

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
open-source-legislation/
├── src/
│   ├── scrapers/
│   │   ├── us/
│   │   │   ├── (states)/           # Organizing directory
│   │   │   │   ├── {state}/        # e.g., ca, ny, tx
│   │   │   │   │   └── statutes/
│   │   │   │   │       ├── read{STATE}.py    # Phase 1: Extract TOC links
│   │   │   │   │       ├── scrape{STATE}.py  # Phase 2: Scrape content
│   │   │   │   │       ├── process{STATE}.py # Phase 3: Generate embeddings
│   │   │   │   │       └── data/             # Scraped data (gitignored)
│   │   │   └── federal/
│   │   │       ├── usc/            # US Code
│   │   │       ├── ecfr/           # Electronic Code of Federal Regulations
│   │   │       └── aim/            # Aeronautical Information Manual
│   │   └── mhl/                    # Other countries (e.g., Marshall Islands)
│   │       └── federal/
│   ├── 1_SCRAPE_TEMPLATE/          # Template for new scrapers
│   │   ├── 1_read.py
│   │   ├── 2_scrape_regular.py
│   │   ├── 2a_scrape_selenium.py   # For JavaScript-heavy sites
│   │   └── 3_process.py
│   ├── utils/
│   │   ├── pydanticModels.py       # Core data models (Node, NodeID, NodeText)
│   │   ├── scrapingHelpers.py      # Scraping utilities & node insertion
│   │   ├── processingHelpers.py    # Embedding generation (batch processing)
│   │   ├── utilityFunctions.py     # Database, API clients, chat completion
│   │   ├── legislation_metadata.json # Jurisdiction metadata & status
│   │   └── api_pricing.json        # API cost tracking
│   └── github/
│       ├── progressTracker.py      # Auto-generate status tables
│       ├── scraper_status.json     # Current scraper status
│       └── status_table.md         # Markdown status table
├── docs/
├── deprecated/
├── public/                         # Images for README
├── requirements.txt
├── .env                           # Database & API credentials (gitignored)
├── CLAUDE.md                      # This file
├── README.md
└── contributing.md
```

**Important Notes:**
- Directories in parentheses like `(states)` are organizational only - they help group related scrapers but are filtered out when parsing paths
- Each scraper follows the naming pattern `{ACTION}{STATE_CODE}.py` (e.g., `readCA.py`, `scrapeTX.py`)
- The `data/` directory in each scraper is gitignored and stores intermediate scraping results

## Common Development Tasks

### Environment Setup

1. **Clone and Setup Virtual Environment:**
   ```bash
   git clone https://github.com/spartypkp/open-source-legislation.git
   cd open-source-legislation

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Set Python Path:**
   ```bash
   # Adjust path to your actual repository location
   export PYTHONPATH=/path/to/open-source-legislation:$PYTHONPATH
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the project root with the following variables:
   ```bash
   # Database Configuration (PostgreSQL)
   DB_NAME=your_database_name
   DB_HOST=localhost  # or your database host
   DB_USERNAME=your_username
   DB_PASSWORD=your_password
   DB_PORT=5432  # default PostgreSQL port

   # API Keys (for embedding generation and processing)
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key  # if using Anthropic
   ```

4. **Database Setup:**
   ```bash
   # Connect to PostgreSQL and create database
   psql -U postgres
   CREATE DATABASE your_database_name;

   # Enable pgvector extension (REQUIRED for embeddings)
   \c your_database_name
   CREATE EXTENSION vector;
   \q
   ```

**Note:** The `.env` file is gitignored. Never commit credentials to the repository.

### Running Scrapers

Scrapers follow a 3-phase pipeline that must be executed in order:

```bash
# Navigate to specific scraper directory
# Example for California statutes
cd src/scrapers/us/\(states\)/ca/statutes/

# Phase 1: Read top-level title links from Table of Contents
python readCA.py
# Output: Creates data/top_level_title_links.json with all title URLs

# Phase 2: Scrape all legislation content
python scrapeCA.py
# Output: Inserts nodes into database table (us_ca_statutes)
# Note: Some scrapers use Selenium (2a_scrape_selenium.py) for JavaScript-heavy sites

# Phase 3: Generate embeddings and process relationships
python processCA.py
# Output: Adds embeddings, updates node relationships (children, siblings)
```

**Important Notes:**
- Each phase depends on the previous one completing successfully
- Phase 2 creates the database table if it doesn't exist
- Phase 3 requires API keys (OpenAI/Anthropic) for embedding generation
- Phase 3 processes nodes in batches (default: 100 nodes at a time)

### Database Operations

**Working with SQL Dumps:**
```bash
# Download and run SQL file for a specific corpus
# Example: Arizona statutes
psql -U your_username -d your_database -f us_az_statutes.sql

# This creates the table and populates all nodes with pre-generated embeddings
```

**Querying Legislation:**
```bash
# Connect to database
psql -U your_username -d your_database

# Example queries
SELECT node_id, node_name, level_classifier
FROM us_ca_statutes
WHERE level_classifier = 'section'
LIMIT 10;

# Search by similarity (requires pgvector)
SELECT node_id, node_name,
       1 - (node_text_embedding <=> '[your_vector]'::vector) as similarity
FROM us_ca_statutes
WHERE node_text_embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 5;
```

### Creating New Scrapers

Follow this comprehensive workflow when adding a new jurisdiction. For full details, see `contributing.md`.

**Phase 0: Research (Before Coding)**
1. Locate the jurisdiction's official statutes website
2. Find the Table of Contents page with all top-level titles
3. Navigate to a sample section to understand the hierarchy (e.g., Title → Chapter → Section)
4. Examine HTML structure and identify containers/tags for each level
5. Identify "reserved" language (e.g., "repealed", "reserved", "renumbered")
6. Determine if the site requires Selenium (JavaScript-rendered content)

**Phase 1: Setup Template**
1. Clone the template:
   ```bash
   # Example for adding Montana (mt) statutes
   mkdir -p src/scrapers/us/\(states\)/mt/statutes
   cp src/1_SCRAPE_TEMPLATE/* src/scrapers/us/\(states\)/mt/statutes/
   ```

2. Rename template files:
   ```bash
   cd src/scrapers/us/\(states\)/mt/statutes/
   mv 1_read.py readMT.py
   mv 2_scrape_regular.py scrapeMT.py
   mv 3_process.py processMT.py
   # Delete 2a_scrape_selenium.py if not needed
   ```

3. Update global variables in each file:
   ```python
   # In readMT.py, scrapeMT.py, processMT.py
   TABLE_NAME = "us_mt_statutes"
   TOC_URL = "https://leg.mt.gov/bills/mca/title_index.html"  # Example
   BASE_URL = "https://leg.mt.gov"  # Example
   ```

4. Create data directory:
   ```bash
   mkdir data
   ```

**Phase 2: Implement Read Function (1_read.py)**
- Extract all top-level title links from TOC page
- Save to `data/top_level_title_links.txt` or `.json`
- Example output: List of URLs to each top-level title

**Phase 3: Implement Scraper (2_scrape_regular.py)**
Choose scraping method based on site structure:
- **Regular Method:** Separate functions for each level (Title → Chapter → Section)
- **Recursive Method:** Single function that calls itself for nested structures
- **Stack Method:** Stack-based approach for single-page hierarchies
- **Selenium Method:** Use `2a_scrape_selenium.py` for JavaScript-heavy sites

Key scraper tasks:
- Parse each level's container
- Extract node information (name, number, links, text)
- Handle reserved/repealed sections
- Use `insert_node()` helper for database insertion
- Handle duplicates with version numbers (`-v_2`, `-v_3`)

**Phase 4: Debug and Test**
- Start with one top-level title to test logic
- Add print statements for debugging
- Perform spot checks at different levels
- Verify node relationships (parent, children)
- Check for edge cases (reserved sections, special formatting)

**Phase 5: Process and Generate Embeddings (3_process.py)**
- Run embedding generation for all nodes with text
- Update node relationships (direct_children, siblings)
- Verify embeddings are created correctly
- Handle API rate limits and batch processing

### Key Utilities

**utilityFunctions.py - Database and API Functions:**
```python
# Database operations (uses psycopg3)
# Requires .env variables: DB_NAME, DB_HOST, DB_USERNAME, DB_PASSWORD, DB_PORT
from src.utils import utilityFunctions as util

# Insert Pydantic models directly to database
nodes = [node1, node2, node3]
util.pydantic_insert(table_name="us_ca_statutes", models=nodes)

# Query database, returns Pydantic models
results = util.pydantic_select(
    table_name="us_ca_statutes",
    model_class=Node,
    where_clause="level_classifier = 'section'"
)

# Standard SQL queries
rows = util.regular_select(
    table_name="us_ca_statutes",
    sql_logic="SELECT * FROM us_ca_statutes LIMIT 10"
)

# Create embeddings (uses OpenAI API)
text = "This is sample legislation text"
embedding_vector = util.create_embedding(text)  # Returns list of floats

# Chat completion API (supports OpenAI, Anthropic, Instructor)
from src.utils.pydanticModels import APIParameters, ChatMessage

params = APIParameters(
    vendor="openai",  # or "anthropic" or "instructor"
    model="gpt-4",
    messages=[ChatMessage(role="user", content="Analyze this law")],
    temperature=0.7
)
response, usage = util.create_chat_completion(params, user="scraper_process")
```

**scrapingHelpers.py - Web Scraping and Node Management:**
```python
from src.utils.scrapingHelpers import insert_node, insert_jurisdiction_and_corpus_node
from src.utils.scrapingHelpers import get_url_as_soup, get_text_clean
from src.utils.pydanticModels import Node

# Create jurisdiction and corpus nodes (run once per scraper)
corpus_node = insert_jurisdiction_and_corpus_node(
    country_code="us",
    jurisdiction_code="mt",
    corpus_code="statutes"
)

# Insert nodes with automatic duplicate handling
node = Node(
    id="us/mt/statutes/title=1/section=1-1-101",
    node_type="content",
    level_classifier="section",
    node_name="Short title",
    parent="us/mt/statutes/title=1"
)
insert_node(
    node=node,
    table_name="us_mt_statutes",
    ignore_duplicate=False,  # Creates versions (-v_2, -v_3) for duplicates
    debug_mode=True  # Prints insertion progress
)

# Fetch URL as BeautifulSoup with retry logic (uses tenacity)
soup = get_url_as_soup("https://example.com/statute/1-1-101")

# Clean extracted text (removes extra whitespace, newlines)
raw_text = "  This is   \n\n  legislation text  "
clean_text = get_text_clean(raw_text)  # "This is legislation text"
```

**processingHelpers.py - Embedding Generation:**
```python
from src.utils.processingHelpers import (
    read_rows_sequentially,
    generate_embeddings_in_batch,
    update_rows_in_batch
)

# Process embeddings in batches (default: 100 at a time)
table_name = "us_mt_statutes"

while True:
    # Fetch batch of nodes without embeddings
    rows = read_rows_sequentially(table_name)
    if not rows or len(rows) == 0:
        break

    # Generate embeddings in parallel (max_workers=10)
    processed_rows = generate_embeddings_in_batch(rows, max_workers=10)

    # Update database with new embeddings
    update_rows_in_batch(processed_rows, table_name)
```

**pydanticModels.py - Core Data Models:**
```python
from src.utils.pydanticModels import Node, NodeID, NodeText

# NodeID - Hierarchical identifier with helper methods
node_id = NodeID(raw_id="us/ca/statutes")
node_id = node_id.add_level(level_classifier="title", level_number="1")
# Result: "us/ca/statutes/title=1"

node_id = node_id.add_level(level_classifier="section", level_number="100")
# Result: "us/ca/statutes/title=1/section=100"

current_level = node_id.current_level  # ("section", "100")
parent_level = node_id.parent_level    # ("title", "1")
parent_id = node_id.pop_level()        # Returns NodeID without last level

# Node - Core legislation model
node = Node(
    id="us/ca/statutes/title=1/section=100",
    node_type="content",  # "structure" or "content"
    level_classifier="section",  # title, chapter, section, etc.
    node_name="Definitions",
    node_number="100",
    parent="us/ca/statutes/title=1",
    link="https://leginfo.legislature.ca.gov/...",
    node_text=["Paragraph 1 text", "Paragraph 2 text"],
    status="valid",  # or "reserved", "repealed", etc.
    core_metadata={"source": "official", "year": "2024"}
)

# NodeText - Paragraph-based text with reference tracking
node_text = NodeText()
node_text.add_paragraph(text="First paragraph", citation_dict={})
node_text.add_paragraph(text="Second paragraph with reference", citation_dict={"ref1": "..."})

## Testing and Quality Assurance

**Pre-scraping Validation:**
- Verify TOC_URL and BASE_URL are correct
- Test that `read.py` successfully extracts all top-level title links
- Check for reserved/repealed language patterns in sample nodes

**During Scraping:**
- Start with a single top-level title to validate logic
- Add print statements showing current node being processed
- Monitor for HTTP errors, timeouts, or HTML parsing failures
- Check database to verify nodes are being inserted correctly

**Post-scraping Validation:**
```python
# Check total node counts
SELECT level_classifier, COUNT(*)
FROM us_mt_statutes
GROUP BY level_classifier;

# Verify parent-child relationships
SELECT node_id, parent
FROM us_mt_statutes
WHERE parent IS NULL AND level_classifier != 'corpus';  # Should be empty

# Check for orphaned nodes (parent doesn't exist)
SELECT a.node_id, a.parent
FROM us_mt_statutes a
LEFT JOIN us_mt_statutes b ON a.parent = b.node_id
WHERE a.parent IS NOT NULL AND b.node_id IS NULL;
```

**Common Issues:**
- Reserved sections: Ensure `status` field is set to "reserved" or "repealed"
- Duplicate nodes: Check for version numbers (`-v_2`, `-v_3`) in node_id
- Missing text: Verify `node_text` is properly extracted for content nodes
- Broken links: Validate URL construction (BASE_URL + relative path)
- Text cleaning: Ensure proper removal of HTML tags and extra whitespace

**Spot Checking:**
Manually verify a sample of nodes at each level:
- First section in first title
- Middle section in middle title
- Last section in last title
- At least one reserved/repealed section

## Progress Tracking and Metadata

The repository includes an automated progress tracking system:

**progressTracker.py:**
- Automatically scans `src/scrapers/` directory for all scraper files
- Updates `src/github/scraper_status.json` with current status
- Generates markdown status table for README.md
- Reads metadata from `src/utils/legislation_metadata.json`

**To update scraper status:**
1. Edit `src/utils/legislation_metadata.json`:
   ```json
   {
     "us": {
       "description": "United States",
       "mt": {
         "description": "Montana",
         "statutes": {
           "description": "Montana Code Annotated",
           "download_link_available": true,
           "status": "Complete",
           "status_description": "Scraper complete, all tests passing",
           "last_updated": "2024-11-14T12:00:00",
           "file_path": "src/scrapers/us/(states)/mt/statutes"
         }
       }
     }
   }
   ```

2. Run the progress tracker:
   ```bash
   python src/github/progressTracker.py
   ```

**Status Values:**
- 🔵 "Planning" - Initial planning phase
- 🔵 "In Progress" - Actively being developed
- 🟡 "Testing" - Scraper complete, undergoing testing
- 🟠 "Refactoring" - Being updated to new schema
- 🟢 "Complete" - Scraper complete, SQL dump available

## Database Schema and Architecture

**Table Structure:**
Each corpus gets its own table: `{country}_{jurisdiction}_{corpus}`

**Key Fields in Node Table:**
- `node_id` (TEXT, PRIMARY KEY): Hierarchical identifier
- `node_type` (TEXT): "structure" or "content"
- `level_classifier` (TEXT): title, chapter, section, etc.
- `node_name` (TEXT): Human-readable name
- `node_number` (TEXT): Numeric/alphanumeric identifier at this level
- `parent` (TEXT): Parent node_id (foreign key reference)
- `link` (TEXT): URL to official source
- `node_text` (TEXT[]): Array of paragraph text
- `node_text_embedding` (VECTOR): Embedding vector (requires pgvector)
- `citation_dict` (JSONB): References to other nodes
- `node_tags` (JSONB): Metadata tags
- `status` (TEXT): valid, reserved, repealed, etc.
- `core_metadata` (JSONB): Additional metadata

**Graph Relationships:**
- Hierarchical: parent → children relationships
- Cross-references: tracked via `citation_dict`
- Siblings: nodes sharing the same parent
- Cross-corpus: references between different legislation bodies

**Database Connection:**
The system uses environment variables from `.env` file:
```python
# Database connection is handled by utilityFunctions.py
# It reads: DB_NAME, DB_HOST, DB_USERNAME, DB_PASSWORD, DB_PORT
# Supports both local PostgreSQL and cloud deployment (Supabase)
```

## Common Patterns and Best Practices

**When writing scrapers:**

1. **Always use scrapingHelpers functions:**
   ```python
   from src.utils.scrapingHelpers import insert_node, get_url_as_soup
   # Don't use raw requests/BeautifulSoup unless necessary
   ```

2. **Handle reserved sections explicitly:**
   ```python
   if "reserved" in node_name.lower() or "repealed" in node_name.lower():
       node.status = "reserved"
       node.node_text = None  # No text for reserved nodes
   ```

3. **Build NodeID incrementally:**
   ```python
   corpus_id = NodeID(raw_id=f"{country}/{jurisdiction}/{corpus}")
   title_id = corpus_id.add_level("title", title_number)
   section_id = title_id.add_level("section", section_number)
   ```

4. **Use batch processing for efficiency:**
   ```python
   nodes_batch = []
   for item in items:
       node = create_node(item)
       nodes_batch.append(node)
       if len(nodes_batch) >= 100:
           util.pydantic_insert(table_name, nodes_batch)
           nodes_batch = []
   # Don't forget remaining nodes
   if nodes_batch:
       util.pydantic_insert(table_name, nodes_batch)
   ```

5. **Add comprehensive error handling:**
   ```python
   try:
       soup = get_url_as_soup(url)
   except Exception as e:
       print(f"Failed to fetch {url}: {e}")
       continue  # Skip this node and continue
   ```

**When debugging scrapers:**
- Use `debug_mode=True` in `insert_node()` to see all insertions
- Print current position in hierarchy: `print(f"Processing: {node_id.raw_id}")`
- Check BeautifulSoup parsing: `print(soup.prettify())` on small sections
- Verify URL construction: `print(f"Fetching: {url}")` before each request

## Dependencies and Requirements

**Core Python Packages (requirements.txt):**
- `beautifulsoup4` (4.12.2): HTML parsing
- `lxml` (4.9.3): XML/HTML parser for BeautifulSoup
- `requests` (2.31.0): HTTP requests
- `psycopg` (2.9.9): PostgreSQL database adapter (psycopg3)
- `pydantic` (2.5.2): Data validation and models
- `openai` (1.3.5): OpenAI API for embeddings
- `anthropic`: Anthropic API (optional)
- `instructor`: Pydantic-based LLM outputs (optional)
- `selenium`: Browser automation for JavaScript sites (optional)
- `tenacity` (8.2.3): Retry logic for web requests
- `tiktoken` (0.5.1): Token counting for OpenAI
- `supabase` (2.1.0): Supabase client for cloud deployment
- `tqdm` (4.66.1): Progress bars

**System Requirements:**
- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- 8GB+ RAM recommended for embedding generation
- Internet connection for scraping and API calls

**Optional:**
- Chrome/Chromium for Selenium-based scrapers
- ChromeDriver matching your Chrome version

## Troubleshooting Common Issues

**Import Errors:**
```bash
# ModuleNotFoundError: No module named 'src'
export PYTHONPATH=/path/to/open-source-legislation:$PYTHONPATH

# On Windows
set PYTHONPATH=C:\path\to\open-source-legislation;%PYTHONPATH%
```

**Database Connection Issues:**
```python
# Error: connection refused / could not connect to server
# Check: .env file exists with correct DB credentials
# Check: PostgreSQL is running
sudo service postgresql status  # Linux
brew services list  # macOS

# Error: relation does not exist
# Check: Table name is correct (e.g., us_mt_statutes)
# Check: Table was created during scraping phase
```

**pgvector Extension Issues:**
```sql
-- Error: type "vector" does not exist
-- Solution: Install pgvector extension
CREATE EXTENSION vector;

-- If installation fails, install pgvector:
-- Ubuntu/Debian:
sudo apt install postgresql-14-pgvector

-- macOS (Homebrew):
brew install pgvector
```

**API Key Issues:**
```bash
# Error: OpenAI API key not found
# Check: .env file contains OPENAI_API_KEY
# Check: .env is in project root, not in src/

# Verify .env is being loaded:
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

**Scraping Errors:**
```python
# HTTP 403 Forbidden
# Some sites block automated requests
# Solution: Add headers or use Selenium scraper
headers = {'User-Agent': 'Mozilla/5.0...'}
response = requests.get(url, headers=headers)

# BeautifulSoup returns None
# HTML structure may have changed
# Solution: Inspect current HTML with browser dev tools
# Update selectors in scraper code

# UnicodeDecodeError
# Solution: Specify encoding
response.text.encode('utf-8').decode('utf-8', errors='ignore')
```

**Embedding Generation Issues:**
```python
# Rate limit errors from OpenAI
# Solution: Reduce max_workers in batch processing
processed_rows = generate_embeddings_in_batch(rows, max_workers=5)  # Lower from 10

# Out of memory during processing
# Solution: Reduce BATCH_SIZE in processingHelpers.py
BATCH_SIZE = 50  # Lower from 100
```

## Project Structure Conventions

**File Naming:**
- Scrapers: `{action}{STATE_ABBREV}.py` (e.g., `readCA.py`, `scrapeTX.py`)
- Tables: `{country}_{jurisdiction}_{corpus}` (e.g., `us_ca_statutes`)
- Node IDs: `{country}/{jurisdiction}/{corpus}/level=value` (e.g., `us/ca/statutes/title=1/section=100`)

**Directory Organization:**
- Parentheses `()` in directory names are for organization only
- They're filtered out during path parsing
- Example: `us/(states)/ca` → parses as `us/ca`

**Allowed Level Classifiers:**
Common values (jurisdiction-specific):
- `title`, `chapter`, `article`, `part`, `section`, `subsection`, `paragraph`
- `division`, `book`, `heading`, `subheading`
- Defined in `pydanticModels.py` as `ALLOWED_LEVELS`

## AI Assistant Workflow Tips

**When asked to create a new scraper:**
1. Start with Phase 0 research - analyze the jurisdiction's website
2. Clone template and set up directory structure
3. Implement read.py first to get all top-level links
4. Test read.py before moving to scrape.py
5. Implement scraper incrementally (one level at a time)
6. Run frequent spot checks during development
7. Only move to process.py after scraping is complete and validated

**When asked to debug an existing scraper:**
1. Read the scraper code to understand its approach
2. Check recent HTML changes on the source website
3. Test each phase independently (read → scrape → process)
4. Use database queries to verify data integrity
5. Look for common issues: URL construction, HTML parsing, reserved sections

**When asked to refactor a scraper:**
1. Check if it follows the current 3-phase architecture
2. Verify it uses utility functions from scrapingHelpers
3. Ensure proper error handling and retry logic
4. Update to use current Pydantic models
5. Test thoroughly after refactoring

## Additional Resources

- **Project Repository:** https://github.com/spartypkp/open-source-legislation
- **Contributing Guide:** See `contributing.md` for detailed scraper development workflow
- **README:** See `README.md` for project overview and download links
- **Status Table:** Check `src/github/status_table.md` for current scraper status
- **Refactoring Docs:** See `docs/refactoring.md` for schema migration info

**Related Projects:**
- Ask Abe AI: https://www.askabeai.com/ (LLM legal education assistant built on this data)

**External Documentation:**
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Pydantic: https://docs.pydantic.dev/latest/
- pgvector: https://github.com/pgvector/pgvector
- psycopg3: https://www.psycopg.org/psycopg3/docs/