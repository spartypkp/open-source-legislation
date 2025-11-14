# ⚠️ PROJECT ARCHIVED - NO LONGER MAINTAINED ⚠️

<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

## Status: Officially Dead

**This project is no longer maintained, developed, or supported.**

Development ceased in August 2024. The infrastructure has been shut down, all download links are broken, and the scrapers are likely outdated. This repository is preserved as an educational reference only.

---

## What This Was

Open-source-legislation was an ambitious attempt to democratize access to global legislative data. The vision was to scrape, process, and standardize legislation from 50+ jurisdictions into a unified SQL format with LLM-ready embeddings, making it easy for developers to build legal applications without the typical barriers of accessing primary source legislative data.

### What Was Accomplished

- **9 complete jurisdiction scrapers** with working SQL dumps at the time (AL, AZ, CA, CT, DE, FL, ID, IL, IN, VA)
- **50+ partial scrapers** in various states of completion
- **Unified PostgreSQL schema** with pgvector support for embeddings
- **Pydantic-based data models** for validation and type safety
- **3-phase scraping architecture** (Read → Scrape → Process)
- **Hierarchical node-based legislation modeling** with cross-corpus references
- **Ask Abe AI** - A legal education assistant that used this data (also shut down)

---

## What's Broken

**Everything that matters for production use:**

1. **All SQL download links are dead** - The Supabase storage hosting was shut down. Every download link in the old documentation returns 404.

2. **Ask Abe AI is down** - The companion legal education application that validated this approach has been shut down.

3. **Scrapers are likely outdated** - Government websites change their HTML structure constantly. Scrapers that worked in 2024 may not work anymore.

4. **No hosted database** - There's no live database with current legislation data.

5. **No support or maintenance** - Issues won't be addressed, pull requests won't be reviewed, and the code won't be updated.

6. **API costs** - Generating embeddings requires OpenAI API access (costs money per run).

---

## Why It Failed

**Honest reflection on what went wrong:**

1. **Unsustainable maintenance burden** - Legislative websites change constantly, requiring ongoing scraper updates. This is a full-time job disguised as a side project.

2. **Scope was too ambitious** - 50+ jurisdictions × constant changes = endless work for a solo developer.

3. **Infrastructure costs** - Hosting SQL dumps and running embedding generation APIs costs real money without a revenue model.

4. **No validated market need** - Despite the noble goal, there wasn't sufficient user adoption (12 GitHub stars) to justify the effort.

5. **Developer moved on** - I built this to support Ask Abe AI. When I stopped needing it, I stopped maintaining it.

---

## Educational Value

**Why this code is still worth looking at:**

This codebase contains solid patterns for legislative web scraping and data modeling that may be useful as reference material:

### 1. Web Scraping Architecture

The **3-phase pipeline** is a clean pattern for large-scale scraping:

- **Phase 1 (Read)**: Extract top-level links from table of contents
- **Phase 2 (Scrape)**: Recursively scrape legislative content with multiple strategies
- **Phase 3 (Process)**: Generate embeddings and establish node relationships

See `src/1_SCRAPE_TEMPLATE/` for the template structure.

### 2. Pydantic Data Models

`src/utils/pydanticModels.py` demonstrates:
- Hierarchical identifier systems (NodeID)
- Validation for complex nested legal structures
- Cross-reference tracking (NodeText with citations)
- Type-safe data pipelines

### 3. PostgreSQL + pgvector Schema

Shows how to model hierarchical legislation as a graph:
- Node-based architecture (structure vs content nodes)
- Parent-child relationships with cross-corpus references
- Vector embeddings for semantic search
- JSONB for flexible metadata

See `CLAUDE.md` for detailed schema documentation.

### 4. Scraping Patterns

Multiple scraping strategies in `src/scrapers/`:
- **Regular method**: Separate functions per hierarchy level
- **Recursive method**: Single function for nested structures
- **Stack method**: Stack-based traversal for single-page hierarchies
- **Selenium method**: For JavaScript-heavy sites

### 5. Utility Functions

`src/utils/` contains reusable helpers:
- `scrapingHelpers.py`: Retry logic, node insertion, duplicate handling
- `processingHelpers.py`: Batch embedding generation
- `utilityFunctions.py`: Database operations, API clients

---

## If You Want to Use This Code

**You're welcome to fork and revive this project, but be aware:**

### What You'll Need

1. **PostgreSQL database** with pgvector extension
2. **OpenAI API key** for embedding generation (costs money)
3. **Time and patience** to fix broken scrapers
4. **Ongoing maintenance commitment** - this isn't a one-time setup

### Reality Check

- **Scrapers will need updates** - Government websites have likely changed since 2024
- **No SQL dumps available** - You'll need to run all scrapers yourself
- **API costs add up** - Generating embeddings for 50 states isn't cheap
- **You're on your own** - Don't expect support or guidance

### How to Get Started

If you still want to try:

```bash
# Clone the repository
git clone https://github.com/spartypkp/open-source-legislation.git
cd open-source-legislation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL with pgvector
# CREATE EXTENSION vector;

# Create .env file with credentials
# DB_NAME, DB_HOST, DB_USERNAME, DB_PASSWORD, DB_PORT
# OPENAI_API_KEY

# Try running a scraper (may not work)
cd src/scrapers/us/\(states\)/ca/statutes/
python readCA.py    # Extract table of contents
python scrapeCA.py  # Scrape content
python processCA.py # Generate embeddings
```

See `CLAUDE.md` for detailed technical documentation (note: it was written when the project was active, so adjust expectations accordingly).

---

## Looking for Alternatives?

**I don't have great answers here, but some thoughts:**

Legislative data scraping is genuinely hard. The challenges that killed this project aren't unique to me:

- **Government websites aren't designed for programmatic access** - They change constantly, use inconsistent formats, and sometimes actively prevent scraping
- **No universal standard** - Every jurisdiction does things differently
- **Maintenance is the real cost** - Initial scraping is easy; keeping it working is brutal

**Possible approaches:**

1. **Use official APIs when they exist** - Some jurisdictions offer official legislative data APIs (rare but valuable)
2. **Focus on one jurisdiction** - Don't try to do 50+ states like I did
3. **Check for existing services** - There may be paid legal data providers that handle maintenance for you
4. **Use LLMs differently** - Instead of pre-processing all legislation, use on-demand scraping + LLM analysis

I don't have specific service recommendations, but I'd encourage looking for solutions that someone else is maintaining.

---

## Technical Architecture (For Reference)

<div align="center">
 <img  width="80%" height="80%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulkdata.png?raw=true">
</div>

### Unified Schema

Legislation is modeled as a hierarchical node graph:

- **Country/Jurisdiction/Corpus** structure (e.g., `us/ca/statutes`)
- **Node types**: Structure (chapters, titles) vs Content (sections with text)
- **Hierarchical IDs**: `us/ca/statutes/title=1/chapter=2/section=3`
- **Cross-references**: Nodes can reference other nodes within or across corpora

<div align="center">
<img  width="70%" height="70%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/cfr-reference.png?raw=true">
</div>

### LLM Readiness

The schema was designed for LLM applications:

- **Pre-generated embeddings** (via OpenAI API)
- **Vector similarity search** (pgvector)
- **Structured metadata** for prompt engineering
- **Citation tracking** for source attribution

<div align="center">
<img width="30%" height="30%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/embedding-fields.png?raw=true">
</div>

### Pydantic Models

Type-safe data handling with validation:

<div align="center">
<img  width="50%" height="50%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/pydantic-model.png?raw=true">
</div>

---

## Repository Structure

```
open-source-legislation/
├── src/
│   ├── scrapers/
│   │   ├── us/
│   │   │   ├── (states)/           # State-level scrapers
│   │   │   └── federal/            # Federal legislation
│   │   └── mhl/                    # Marshall Islands
│   ├── 1_SCRAPE_TEMPLATE/          # Template for new scrapers
│   └── utils/
│       ├── pydanticModels.py       # Core data models
│       ├── scrapingHelpers.py      # Scraping utilities
│       ├── processingHelpers.py    # Embedding generation
│       └── utilityFunctions.py     # Database & API clients
├── docs/
├── deprecated/
├── public/                         # Documentation images
├── CLAUDE.md                       # Detailed technical docs
├── requirements.txt
└── README.md                       # This file
```

---

## Final Thoughts

This project represents a lot of work and good intentions. The code quality is solid, the architecture is sound, and the vision was noble. It failed not because of bad engineering, but because the problem is genuinely hard and the scope was unsustainable for unfunded solo development.

If you're interested in legislative data access, I hope this code provides useful patterns. If you want to revive the project, you have my blessing—just know what you're getting into.

If you're me from the future looking back at this: you learned a lot building this, even if it didn't work out. That's worth something.

---

**Project Timeline:**
- Active development: 2023-2024
- Last significant update: August 2024
- Infrastructure shutdown: 2024
- Officially archived: November 2025

**License:** MIT (use the code however you want)

**Created by:** [@spartypkp](https://github.com/spartypkp)

---

## Additional Resources

- [CLAUDE.md](CLAUDE.md) - Comprehensive technical documentation (written when project was active)
- [deprecated/README.md](deprecated/README.md) - Historical documentation
- [docs/refactoring.md](docs/refactoring.md) - Schema migration notes

For questions or interest in reviving this project, feel free to open an issue. I may not respond quickly, but I'm not completely ghost.
