<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

# Open Sourcing the World's Legislation

Welcome to open-source-legislation, a project which aims to provide access to global primary source legislation for all. The heart of the project is a Python based platform of webscrapers, individually tailored for each jurisdiction and corpus of legislation. We provide the capability to run these scrapers yourself, and populate your own SQL database of cleaned and processed primary source legislation. 

<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulk-data.png?raw=true">
We propose a unified schema for representing legislation as a hierarchical graph of nodes which creates a rich knowledge graph for each jurisdiction, specifically designed for use with Large Language Models. Soon we will offer bulk data downloads for all primary source legislation, as well as Python and Typescript SDKs for immediate and easy usage.
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/supabase-example.png?raw=true">

## Democratizing Legal Knowledge for All

Our dream is to curate a platform and community dedicated to providing primary source legislation data in a unified and accessible format. Building applications in the legal field is difficult considering the incredible barriers to accessing legislation data in a standardized format for use with code. A legal engineer wanting to build an application which relies on primary source legislation would first need to spend considerable time and effort sourcing this legislative data before they could even begin to build. We want to remove these barriers, and provide instant and easy access so that our community can just start building. We believe legal data and law itself is a public good, and should be readily and easily accessible for all.

## Bulk Data Downloads
We aim to provide bulk data downloads of primary source legislation for every supported jurisdiction and corpus. ** ADD EXAMPLES ** 

## Running Scrapers Locally
You can also run scrapers locally. **TODO**

## Using Legislation Data
**TODO**
### Python SDK
**TODO**
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/pydantic-model.png?raw=true">
### Typescript SDK
**TODO**

## About Our Schema
Populating knowledge graph

## Preparing Bulk Data for Usage with LLM
More here

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
