# Contributing to open-source-legislation

Thank you for your interest in contributing to open-source-legislation! We welcome contributions of all kinds, including new features, bug fixes, documentation improvements, and especially new jurisdiction scrapers. This document will guide you through the process of contributing to the project.

## Table of Contents

1. [How to Contribute](#how-to-contribute)
2. [Creating a New Scraper](#creating-a-new-scraper)
    - [Phase 0: Initial Research](#phase-0-initial-research)
    - [Phase 1: Prepare Coding Environment](#phase-1-prepare-coding-environment)
    - [Phase 2: Read Top-level Titles](#phase-2-read-top-level-titles)
    - [Phase 3: Code Scraper](#phase-3-code-scraper)
    - [Phase 4: Debug Scraper](#phase-4-debug-scraper)
    - [Phase 5: Process Database](#phase-5-process-database)
3. [Coding Standards](#coding-standards)
4. [Issue Reporting](#issue-reporting)

# Contributing to open-source-legislation

Thank you for your interest in contributing to open-source-legislation! We welcome contributions of all kinds, including new features, bug fixes, documentation improvements, and especially new jurisdiction scrapers. This document will guide you through the process of contributing to the project.

## Table of Contents

1. [How to Contribute](#how-to-contribute)
2. [Creating a New Scraper](##creating-a-new-scraper)
    - [Phase 0: Initial Research](###phase-0-initial-research)
    - [Phase 1: Prepare Coding Environment](###phase-1-prepare-coding-environment)
    - [Phase 2: Read Top-level Titles](###phase-2-read-top-level-titles)
    - [Phase 3: Code Scraper](###phase-3-code-scraper)
    - [Phase 4: Debug Scraper](###phase-4-debug-scraper)
    - [Phase 5: Process Database](###phase-5-process-database)
3. [Coding Standards](##coding-standards)
4. [Issue Reporting](##issue-reporting)


## How to Contribute

1. **Fork the Repository:**
   - Fork the repository on GitHub.
   - Clone your forked repository to your local machine.
   - Create a new branch for your work.

2. **Set Up Your Development Environment:**
   - Create a virtual environment.
   - Install dependencies from `requirements.txt`.
   - Set up the database (refer to the `README.md` for instructions).

3. **Make Your Changes:**
   - Ensure your code follows our coding standards.
   - Write or update tests as necessary.
   - Document your changes in the code and in the `docs/` directory.

4. **Submit a Pull Request:**
   - Push your changes to your forked repository.
   - Submit a pull request to the `main` branch of the original repository.
   - Provide a clear and descriptive title and description for your pull request.

## Creating New Scrapers

To add a new jurisdiction scraper, follow these detailed steps:

### Phase 0: Initial Research

1. **Find the statutes web page.**
2. **Find the Table of Contents page.**
   - This is where all the `top_level_titles` live.
3. **Find the first section and understand the path to reach it.**
   - Follow the path from top to bottom (usually Title -> Chapter -> Section links).
4. **Determine the format of the legislation (HTML, PDF, Java, mixed).**
5. **Understand the level hierarchy.**
   - Identify the levels (e.g., Title -> Chapter -> Section).
   - Determine if the hierarchy and order are consistent.
6. **Examine the HTML structure.**
   - Identify containers and unique IDs for each level.
   - Note any specific data like node names or links that are well-tagged in the HTML.
7. **Identify reserved language in the node names.**
   - Start a list of terms indicating reserved sections (e.g., "repealed", "reserved", "renumbered").

### Phase 1: Prepare Coding Environment

1. **Find the country/state code for the jurisdiction.**
2. **Clone the `SCRAPE_TEMPLATE` directory.**
3. **Rename template files (e.g., `readTEMPLATE`, `scrapeTEMPLATE`, `processTEMPLATE`).**
4. **Update global variables in the renamed files:**
   - Set `TABLE_NAME` to `code_node` (e.g., `ca_node` for California).
   - Set `TOC_URL` to the Table of Contents URL.
   - Set `BASE_URL` to the base URL of the jurisdiction's website.
5. **Create a table in your database (e.g., using Postico).**

### Phase 2: Read Top_level_titles (`read.py`)

1. **Navigate to the Table of Contents page.**
2. **Open `read(STATE).py` file.**
3. **Create a data folder to store scraped data.**
4. **Inspect the Table of Contents page to identify the HTML container for top-level title links.**
   - Set this container in BeautifulSoup.
5. **Iterate over each `top_level_title` link to extract the link and additional information if necessary.**
   - Save this information to `data/top_level_titles.txt`.

### Phase 2.1: Code Scraper (`scrape.py`)

1. **Open `scrape.py` file.**
2. **Read in top-level titles from the `.txt` file.**
3. **Iterate over each URL and determine the scraping method to use based on the legislation's properties and HTML structure.**
4. **Choose a scraping method (Regular, Recursive, Stack) and delete unused methods.**
5. **Implement the chosen method:**

### Phase 2.2: Code Regular

1. **Create a scrape function for each level (`scrape_level`).**
2. **In each function, create a BeautifulSoup object for the parent container of the level elements.**
3. **Iterate over each level element to extract node information.**
4. **Check for reserved nodes and handle special formatting.**
5. **Insert nodes into the database and handle duplicates.**
6. **Call the next scrape function as needed.**

### Phase 2.3: Code Recursive

1. **Implement the recursive scraping function (`scrape_structure`).**
2. **Handle each level by calling the function recursively until the section level is reached.**
3. **Extract section information and insert it into the database.**

### Phase 2.4: Code Stack

1. **Implement the stack-based scraping function.**
2. **Handle structure nodes on a single page using a stack data structure.**
3. **Extract section information and insert it into the database.**

### Phase 3: Debug Scraper (`scrape.py`)

1. **Add print statements to debug each level and node.**
2. **Incrementally test by adding one level at a time.**
3. **Check for common errors (e.g., mis-tagged reserved nodes, incorrect links, formatting issues).**
4. **Perform thorough spot checks to ensure data integrity.**

### Phase 4: Process Database (`process.py`)

1. **Run the `scrape.py` file to get vector embeddings for all valid nodes.**
2. **Update the `node_direct_children` and `node_siblings` fields using SQL queries.**
3. **Ensure all fields are of the correct type (e.g., `node_text` as Vector, `node_tags` as jsonb).**
4. **Optionally run additional processing modules (e.g., definition extraction, reference extraction).**

### Phase 5: Upload to Cloud - PGADMIN

1. **Connect to your local database server and back it up.**
2. **Disconnect from the local server and connect to Supabase (Postgres).**
3. **Restore the database from the backup.**

## Coding Standards

- **Follow PEP 8 guidelines for Python code.**
- **Use meaningful variable names and consistent naming conventions.**
- **Add type annotations for function arguments and return types.**
- **Document all functions and classes using docstrings.**

## Issue Reporting

If you encounter any issues or have suggestions for improvements, please report them through the GitHub issue tracker. Provide as much detail as possible to help us understand and address the issue.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to create a welcoming and inclusive environment for all contributors.

Thank you for contributing to open-source-legislation! Together, we can build a comprehensive and reliable database of legislative information.
