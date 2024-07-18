<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

# Open Sourcing the World's Legislation

Welcome to open-source-legislation, a project which aims to provide access to global primary source legislation for all. The heart of the project is a Python based platform of webscrapers, individually tailored for each jurisdiction and corpus of legislation. We provide the capability to run these scrapers yourself, and populate your own SQL database of cleaned and processed primary source legislation. 


<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulkdata.png?raw=true">


We propose a unified schema for representing legislation as a hierarchical graph of nodes which creates a rich knowledge graph for each jurisdiction, specifically designed for use with Large Language Models. Soon we will offer bulk data downloads for all primary source legislation, as well as Python and Typescript SDKs for immediate and easy usage.


## Supported Legislation
| Country | Jurisdiction | Corpus | Status | Last Updated | File Path |
|---------|--------------|--------|--------|--------------|-----------|
| mhl | federal | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/mhl/federal/statutes/scrapeMHL.py) |
| us | ak | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ak/statutes/scrapeAK.py) |
| us | al | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/al/statutes/scrapeAL.py) |
| us | az | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/az/statutes/scrapeAZ.py) |
| us | ca | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ca/statutes/scrapeCA.py) |
| us | co | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/co/statutes/scrapeCO.py) |
| us | ct | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ct/statutes/scrapeCT.py) |
| us | de | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/de/statutes/scrapeDE.py) |
| us | federal | ecfr | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/ecfr/scrapeECFR.py) |
| us | federal | usc | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/usc/scrapeUSC.py) |
| us | federal | aim | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/aim/scrapeAIM.py) |
| us | fl | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/fl/statutes/scrapeFL.py) |
| us | hi | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/hi/statutes/scrapeHI.py) |
| us | ia | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ia/statutes/scrapeIA.py) |
| us | id | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/id/statutes/scrapeID.py) |
| us | il | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/il/statutes/scrapeIL.py) |
| us | in | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/in/statutes/scrapeIN.py) |
| us | ks | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ks/statutes/scrapeKS.py) |
| us | ky | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ky/statutes/scrapeKY.py) |
| us | la | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/la/statutes/scrapeLA.py) |
| us | ma | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ma/statutes/scrapeMA.py) |
| us | md | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/md/statutes/scrapeMD.py) |
| us | me | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/me/statutes/scrapeME.py) |
| us | mi | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mi/statutes/scrapeMI.py) |
| us | mn | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mn/statutes/scrapeMN.py) |
| us | mo | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mo/statutes/scrapeMO.py) |
| us | mt | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mt/statutes/scrapeMT.py) |
| us | nc | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nc/statutes/scrapeNC.py) |
| us | nd | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nd/statutes/scrapeND.py) |
| us | ne | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ne/statutes/scrapeNE.py) |
| us | nh | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nh/statutes/scrapeNH.py) |
| us | nm | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nm/statutes/scrapeNM.py) |
| us | ny | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ny/statutes/scrapeNY.py) |
| us | oh | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/oh/statutes/scrapeOH.py) |
| us | or | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/or/statutes/scrapeOR.py) |
| us | pa | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/pa/statutes/scrapePA.py) |
| us | ri | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ri/statutes/scrapeRI.py) |
| us | sc | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sc/statutes/scrapeSC.py) |
| us | sd | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sd/statutes/2a_scrape_selenium.py) |
| us | tx | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/tx/statutes/scrapeTX.py) |
| us | ut | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ut/statutes/scrapeUT.py) |
| us | vt | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/vt/statutes/scrapeVT.py) |
| us | wa | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wa/statutes/scrapeWA.py) |
| us | wi | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wi/statutes/scrapeWI.py) |
| us | wv | statutes | Refactoring | 2024-07-18T12:45:56.681662 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wv/statutes/scrapeWV.py) |

Legislation status tracked in real time.


## Democratizing Legal Knowledge for All

Our dream is to curate a platform and community dedicated to providing primary source legislation data in a unified and accessible format. Building applications in the legal field is difficult considering the incredible barriers to accessing legislation data in a standardized format for use with code. A legal engineer wanting to build an application which relies on primary source legislation would first need to spend considerable time and effort sourcing this legislative data before they could even begin to build. We want to remove these barriers, and provide instant and easy access so that our community can just start building. We believe legal data and law itself is a public good, and should be readily and easily accessible for all.

## Bulk Data Downloads
We aim to provide bulk data downloads of primary source legislation for every supported jurisdiction and corpus. ** ADD EXAMPLES ** 

## Running Scrapers Locally
You can also run scrapers locally. 


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
