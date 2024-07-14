<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/banner-xl.png?raw=true">

# open-source-legislation

Welcome to open-source-legislation, a comprehensive Python-based solution designed for automating the scraping and processing of primary source legislation into an PostgreSQL knowledge graph, ready for use with LLMs. Our dream is to provide a centralized and open platform for developers and legal engineers to freely utilize legislation data. 

## Project Overview

open-source-legislation is an open-source project aimed at scraping primary source legislation data, processing it for use with LLMs (Large Language Models), and loading it into SQL databases. Each legal jurisdiction and corpus of legal document has a separate scraper and processor, which can be run individually or concurrently to directly scrape and process current legislation. The project is currently focused on the scraping and processing of statutes from all US states, the US Federal Jurisdiction, with some experimentation in other global and special legal jurisdictions.

## Installation and Setup

1. **Clone the Repository:**
   ```bash
    git clone https://github.com/your-username/open-source-legislation.git
    cd open-source-legislation
    ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
    ```

4. **Set Up Database:**
   #### CODE BLOCK

## Usage Instructions

To run an existing scraper for a specific jurisdiction (e.g., California statutes):

1. **Navigate to the Scraper Directory:**
   #### CODE BLOCK

2. **Run the Scraper:**
   #### CODE BLOCK

## Contributing

We welcome contributions from the community! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project, including how to add new jurisdictions.

## Key Terms

- **Top_level_title:** The first explicit category used to split up legislation, always found as the first category on a main table of contents page.
- **Reserved:** Indicates that this piece of legislation (structure or content node) is no longer available because the legislature has restructured, renumbered, or repealed it.
- **Soup:** The BeautifulSoup object in Python that contains the HTML of the entire current webpage.


## Additional Resources

- [Documentation](docs/documentation.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contribution Guidelines](CONTRIBUTING.md)

Thank you for your interest in open-source-legislation! Together, we can create a comprehensive database of legislative information.
