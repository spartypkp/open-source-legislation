<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

# Open Sourcing the World's Legislation

Welcome to open-source-legislation, a platform dedicated to democratizing access to global legislative data. This repository serves as a foundational tool for developers, legal professionals, and researchers to build applications using primary source legislation. Download legislation data in our standardized SQL format and immediate start building with our Python and Typescript (Coming Soon!) SDKs. We are striving to eliminate the incredible barriers to accessing primary source legislation data by building a comprehensive library of global legislation.

# Features
1. **Global Repository of Scraped Legislation**: Tap into our extensive database featuring detailed legislative content from countries and jurisdictions worldwide. The bottom line is we want to make this data easy to begin building with.

2. **Download Processed SQL Legislation Data**: Primary source legislation is scraped and processed into SQL files with rich metadata tagging, making it easy to download and integrate directly into your databases. Download one or many different corpus of legislation from different countries and jurisdictions. 

<div align="center">
 <img  width="80%" height="80%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulkdata.png?raw=true">
 </div>

3. **Unified Legislation Schema**: Legislation is modeled within a sophisticated SQL knowledge graph schema, designed to support complex queries and relational data exploration, enhancing both the depth and breadth of legislative analysis. Connections between nodes of legislation in the same corpus and different corpus are now possible, unlocking powerful cross-corpus and cross-jurisdiction connections. Below, is an example Section from the US Code of Federal Regulations, showcasing a Section which contains direct references to other pieces of legislation within the CFR. 

<div align="center">
<img  width="70%" height="70%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/cfr-reference.png?raw=true">
</div>

The scraper file extracts and processes text into our unified schema, which allows for the direct connections between nodes in our graphs. This allows for incredibly powerful graph traversal.

<div align="center">
<img  width="70%" height="70%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/cfr-node_text-reference.png?raw=true">
 </div>

4. **Large Language Model Readiness**: The structure and availability of data are optimized for use with Large Language Models, facilitating advanced computational legal studies and AI-driven applications. Embedding fields are pre-generated and available out of the box (Donations welcome) 

<div align="center">
<img width="30%" height="30%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/embedding-fields.png?raw=true">
</div>

[Ask Abe](https://www.askabeai.com/), a legal education assistant developed in parallel with this project, showcases the capabilities of LLM applications built using open-source-legislation.

<div align="center">
<img width="80%" height="80%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/abe-example.png?raw=true">
</div>

5. **Python SDK**: Utilize our Python SDK based on Pydantic to seamlessly interface with the legislation data. This SDK simplifies the process of data handling the unified schema, making it straightforward to implement robust data pipelines. Pydantic models provide instant data validation, helper functions for data transformation (node_text into JSON, XML, string), and allow for easy integration with the Instructor library for LLM prompting.

<div align="center">
<img  width="50%" height="50%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/pydantic-model.png?raw=true">
</div>

See more documentation in (TODO: Add link to documentation and write documentation)

6. **TypeScript SDK (Coming Soon)**: Anticipate the release of our TypeScript SDK, which will provide additional flexibility for developing client-side applications and services.

7. **Customizable Scraping Tools**: All scraping and processing tools are open-source and fully customizable. Users are encouraged to modify, extend, or enhance these tools to suit their specific needs or to contribute back to the community.

## Supported Legislation
| Country | Jurisdiction | Corpus | | Status   |  Download | Source Code |
|-------------|--------------|------------------|---|-------------|--------------|-------------|
| mhl - Republic of the Marshall Islands | federal - Federal Jurisdiction | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/mhl/federal/statutes) |
| us - United States | ak - Alaska | Statutes | 🟡 | Testing | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ak/statutes) |
| us - United States | al - Alabama | Code of Alabama | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/al/statutes/us_al_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/al/statutes) |
| us - United States | az - Arizona | Statutes | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/az/statutes/us_az_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/az/statutes) |
| us - United States | ca - California | Code | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/ca/statutes/us_ca_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ca/statutes) |
| us - United States | co - Colorado | Statutes | 🔵 | In Progress | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/co/statutes) |
| us - United States | ct - Conneticut | Statutes | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/ct/statutes/us_ct_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ct/statutes) |
| us - United States | de - Delaware | Statutes | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/de/statutes/us_de_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/de/statutes) |
| us - United States | federal - Federal Jurisdiction | Code of Federal Regulations - Electronic | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/ecfr) |
| us - United States | federal - Federal Jurisdiction | US Code | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/usc) |
| us - United States | federal - Federal Jurisdiction | Aeronautical Information Manual | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/aim) |
| us - United States | fl - Florida | Statutes | 🟢 | Complete | [download](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/fl/statutes/us_fl_statutes.sql) |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/fl/statutes) |
| us - United States | hi - Hawaii | Statutes | 🟡 | Testing | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/hi/statutes) |
| us - United States | ia - Iowa | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ia/statutes) |
| us - United States | id - Idaho | Statutes | 🟡 | Testing | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/id/statutes) |
| us - United States | il - Illinois | Statutes | 🟡 | Testing | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/il/statutes) |
| us - United States | in - Indiana | Statutes | 🟡 | Testing | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/in/statutes) |
| us - United States | ks - Kansas | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ks/statutes) |
| us - United States | ky - Kentucky | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ky/statutes) |
| us - United States | la - Louisianna | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/la/statutes) |
| us - United States | ma - Massachussetts | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ma/statutes) |
| us - United States | md - Maryland | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/md/statutes) |
| us - United States | me - Maine | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/me/statutes) |
| us - United States | mi - Michigan | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mi/statutes) |
| us - United States | mn - Minnesota | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mn/statutes) |
| us - United States | mo - Missouri | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mo/statutes) |
| us - United States | mt - Montana | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mt/statutes) |
| us - United States | nc - North Carolina | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nc/statutes) |
| us - United States | nd - North Dakota | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nd/statutes) |
| us - United States | ne - Nebraska | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ne/statutes) |
| us - United States | nh - New Hampshire | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nh/statutes) |
| us - United States | nm - New Mexico | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nm/statutes) |
| us - United States | ny - New York | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ny/statutes) |
| us - United States | oh - Ohio | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/oh/statutes) |
| us - United States | or - Oregon | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/or/statutes) |
| us - United States | pa - Pennsylvania | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/pa/statutes) |
| us - United States | ri - Rhode Island | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ri/statutes) |
| us - United States | sc - South Carolina | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sc/statutes) |
| us - United States | sd - South Dakota | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sd/statutes) |
| us - United States | tx - Texas | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/tx/statutes) |
| us - United States | ut - Utah | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ut/statutes) |
| us - United States | vt - Vermont | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/vt/statutes) |
| us - United States | wa - Washington | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wa/statutes) |
| us - United States | wi - Wisconsin | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wi/statutes) |
| us - United States | wv - West Virginia | Statutes | 🟠 | Refactoring | N/A |  [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wv/statutes) |

Legislation status tracked in real time.


## Downloading Legislation Data 

We aim to provide data downloads of primary source legislation for every supported jurisdiction and corpus. Currently, every supported corpus of legislation has a corresponding .sql file available for download. Running this SQL file will create that corpus's corresponding PostgresSQL file using individual insert statements. Below is an example .SQL file for Arizona Statutes.

<div align="center">
<img width="50%" height="50%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/sql-dump.png?raw=true">
</div>

**Note**: Corpuses with deprecated schema undergoing refactoring can still be accessed, requiring cloning the repository and running the scrapers manually.

### Find and Download the Corpus's .sql File
Go to the "## Supported Legislation" table and click on the link of the requested corpus of legislation Download Link. This is a link to a hosted file storage system which will automatically initiate a download. Hosting legislation for free and public downloads can be financially demanding, consider supporting the project or joining the community!

### Run the SQL File
There are different ways to run the SQL file. I recommend using psql. Below are installation and usage instructions.

#### Prerequesites
1. Postgres is installed
2. PSQL is usable

#### Running the SQL File
Open Terminal or Command Prompt

Navigate to the Directory Containing the .sql File
Use the cd command to navigate to the directory where your .sql file is located.
```sh
cd path/to/your/sql/file
```

Execute the following command to run your .sql file and connect it to your local PostgreSQL database:
```sh
psql -U your_username -d your_database -f country_jurisdiction_corpus.sql
```
Replace your_username with your PostgreSQL username, your_database with the name of your database, and country_jurisdiction_corpus.sql with the name of your .sql file.

#### Example
Assuming your username is myuser, your database name is mydatabase, and your file is named us_az_statutes.sql, the command would be:
```sh
psql -U myuser -d mydatabase -f us_az_statutes.sql
```

This command will prompt you to enter your PostgreSQL password. After entering the password, it will execute the .sql file and populate your database with the data from the file.

By following these steps, you can successfully download and run the .sql files to create tables for each corpus you need in your PostgreSQL database.

## Running Scrapers Locally
Besides downloading data, this repository contains all of the source code on all supported corpus of legislation and the Python based scrapers which scrape, process, and clean the data. You are free to modify, use, and update these programs as you see fit. If you'd prefer to run them yourselves, which would allow for more regular updates, go for it! You can run these scrapers yourself by following these steps.

**Note**: Corpus with deprecated schema undergoing refactoring are only usable by manually running scrapers. We hope to finish refactoring soon, and offer bulk data downloads for all supported corpuses.

### Setup Instructions
1. **Clone the Repository:**
   ```bash
    git clone https://github.com/spartypkp/open-source-legislation.git
    cd open-source-legislation
    ```

2. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
    ```

4. **Set Up Database:**
   Ensure you have PostgresSQL installed and set up on your machine. Populate the database config file (**TODO**)

### Running Scrapers

To run an existing scraper for a specific jurisdiction (e.g., California statutes):

1. **Navigate to the Scraper Directory:**
   Going to the "## Supported Legislation" table, click on the corpus of choice's "Source Code" field. This will take you to the location of the specific scraper within the correct corpus, jurisdiction, and country folder.

2. **Run the Scraper:**
   Run the Python scraper normally.


### Python SDK
**TODO**

### Typescript SDK
**TODO**

## About Our Schema
Populating knowledge graph

## Preparing Bulk Data for Usage with LLM
More here

## Democratizing Legal Knowledge for All

Our dream is to curate a platform and community dedicated to providing primary source legislation data in a unified and accessible format. Building applications in the legal field is difficult considering the incredible barriers to accessing legislation data in a standardized format for use with code. A legal engineer wanting to build an application which relies on primary source legislation would first need to spend considerable time and effort sourcing this legislative data before they could even begin to build. We want to remove these barriers, and provide instant and easy access so that our community can just start building. We believe legal data and law itself is a public good, and should be readily and easily accessible for all.


## Contributing

We welcome contributions from the community! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project, including how to add new countries, jurisdictions, and corpuses.

## Extra Documentation
Mega WIP lol

- **Top_level_title:** The first explicit category used to split up legislation, always found as the first category on a main table of contents page.
- **Reserved:** Indicates that this piece of legislation (structure or content node) is no longer available because the legislature has restructured, renumbered, or repealed it.
- **Soup:** The BeautifulSoup object in Python that contains the HTML of the entire current webpage.


## Additional Resources

- [Documentation](docs/documentation.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contribution Guidelines](CONTRIBUTING.md)

Thank you for your interest in open-source-legislation! Together, we can create a comprehensive database of legislative information.
