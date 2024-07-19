<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

# Open Sourcing the World's Legislation

Welcome to open-source-legislation, a platform dedicated to democratizing access to global legislative data. This repository serves as a foundational tool for developers, legal professionals, and researchers to build applications using primary source legislation. Download legislation data in our standardized SQL format and immediate start building with our Python and Typescript (Coming Soon!) SDKs. We are striving to eliminate the incredible barriers to accessing primary source legislation data by building a comprehensive library of global legislation.

# Features
1. **Global Repository of Scraped Legislation**: Tap into our extensive database featuring detailed legislative content from countries and jurisdictions worldwide. The bottom line is we want to make this data easy to begin building with.

2. **Download Processed SQL Legislation Data**: Primary source legislation is scraped and processed into SQL files with rich metadata tagging, making it easy to download and integrate directly into your databases. Download one or many different corpus of legislation from different countries and jurisdictions. 

 <img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulkdata.png?raw=true">

3. **Unified Legislation Schema**: Legislation is modeled within a sophisticated SQL knowledge graph schema, designed to support complex queries and relational data exploration, enhancing both the depth and breadth of legislative analysis. Connections between nodes of legislation in the same corpus and different corpus are now possible, unlocking powerful cross-corpus and cross-jurisdiction connections. Below, is an example Section from the US Code of Federal Regulations, showcasing a Section which contains direct references to other pieces of legislation within the CFR.
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/cfr-reference.png?raw=true">

Below, is the extracted and processed text in our schema, which allows for the direct connections between nodes in our graphs. This allows for incredibly powerful graph traversal. 

<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/cfr-node_text_reference.png?raw=true">

4. **Large Language Model Readiness**: The structure and availability of data are optimized for use with Large Language Models, facilitating advanced computational legal studies and AI-driven applications. Embedding fields are pre-generated and available out of the box (Donations welcome) 

<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/embedding-fields.png?raw=true">

Ask Abe [view](https://www.askabeai.com/), a legal education assistant developed in parallel with this project, showcases the capabilities of LLM applications built using open-source-legislation.

<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/abe-example.png?raw=true">

5. **Python SDK**: Utilize our Python SDK based on Pydantic to seamlessly interface with the legislation data. This SDK simplifies the process of data handling the unified schema, making it straightforward to implement robust data pipelines. Pydantic models provide instant data validation, helper functions for data transformation (node_text into JSON, XML, string), and allow for easy integration with the Instructor library for LLM prompting.
 <img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/pydantic-model.png?raw=true">

See more documentation in (TODO: Add link to documentation and write documentation)

6. **TypeScript SDK (Coming Soon)**: Anticipate the release of our TypeScript SDK, which will provide additional flexibility for developing client-side applications and services.

7. **Customizable Scraping Tools**: All scraping and processing tools are open-source and fully customizable. Users are encouraged to modify, extend, or enhance these tools to suit their specific needs or to contribute back to the community.

## Supported Legislation
| Country | Jurisdiction | Corpus | | Status | Dev Comment | Last Updated | Source Code | Download |
|---------|--------------|------------------|---|---------|-------------|--------------|-------------|----------|
| mhl - Republic of the Marshall Islands | federal - Federal Jurisdiction | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T15:59:24.920177 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/mhl/federal/statutes) | N/A |
| us - United States | ak - Alaska | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ak/statutes) | N/A |
| us - United States | al - Alabama | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/al/statutes) | N/A |
| us - United States | az - Arizona | statutes - Statutes | 🟡 | Testing |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/az/statutes) | [view](https://jwscgsmkadanioyopaef.supabase.co/storage/v1/object/public/open-source-legislation/us/az/statutes/us_az_statutes.sql) |
| us - United States | ca - California | statutes - Code | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ca/statutes) | N/A |
| us - United States | co - Colorado | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/co/statutes) | N/A |
| us - United States | ct - Conneticut | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ct/statutes) | N/A |
| us - United States | de - Delaware | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/de/statutes) | N/A |
| us - United States | federal - Federal Jurisdiction | ecfr - Code of Federal Regulations - Electronic | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/ecfr) | N/A |
| us - United States | federal - Federal Jurisdiction | usc - US Code | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/usc) | N/A |
| us - United States | federal - Federal Jurisdiction | aim - Aeronautical Information Manual | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/aim) | N/A |
| us - United States | fl - Florida | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/fl/statutes) | N/A |
| us - United States | hi - Hawaii | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/hi/statutes) | N/A |
| us - United States | ia - Iowa | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ia/statutes) | N/A |
| us - United States | id - Idaho | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/id/statutes) | N/A |
| us - United States | il - Illinois | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/il/statutes) | N/A |
| us - United States | in - Indiana | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/in/statutes) | N/A |
| us - United States | ks - Kansas | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ks/statutes) | N/A |
| us - United States | ky - Kentucky | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ky/statutes) | N/A |
| us - United States | la - Louisianna | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/la/statutes) | N/A |
| us - United States | ma - Massachussetts | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ma/statutes) | N/A |
| us - United States | md - Maryland | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/md/statutes) | N/A |
| us - United States | me - Maine | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/me/statutes) | N/A |
| us - United States | mi - Michigan | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mi/statutes) | N/A |
| us - United States | mn - Minnesota | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mn/statutes) | N/A |
| us - United States | mo - Missouri | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mo/statutes) | N/A |
| us - United States | mt - Montana | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mt/statutes) | N/A |
| us - United States | nc - North Carolina | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nc/statutes) | N/A |
| us - United States | nd - North Dakota | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nd/statutes) | N/A |
| us - United States | ne - Nebraska | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ne/statutes) | N/A |
| us - United States | nh - New Hampshire | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nh/statutes) | N/A |
| us - United States | nm - New Mexico | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nm/statutes) | N/A |
| us - United States | ny - New York | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ny/statutes) | N/A |
| us - United States | oh - Ohio | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/oh/statutes) | N/A |
| us - United States | or - Oregon | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/or/statutes) | N/A |
| us - United States | pa - Pennsylvania | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/pa/statutes) | N/A |
| us - United States | ri - Rhode Island | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ri/statutes) | N/A |
| us - United States | sc - South Carolina | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sc/statutes) | N/A |
| us - United States | sd - South Dakota | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sd/statutes) | N/A |
| us - United States | tx - Texas | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/tx/statutes) | N/A |
| us - United States | ut - Utah | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ut/statutes) | N/A |
| us - United States | vt - Vermont | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/vt/statutes) | N/A |
| us - United States | wa - Washington | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wa/statutes) | N/A |
| us - United States | wi - Wisconsin | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wi/statutes) | N/A |
| us - United States | wv - West Virginia | statutes - Statutes | 🟠 | Refactoring |  Major Overhaul WIP | 2024-07-18T14:53:05.618081 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wv/statutes) | N/A |

Legislation status tracked in real time.


## Downloading Legislation Data 
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/sql-dump.png?raw=true">

We aim to provide data downloads of primary source legislation for every supported jurisdiction and corpus. Currently, every supported corpus of legislation has a corresponding .sql file available for download. Running this SQL file will create that corpus's corresponding PostgresSQL file using individual insert statements. Follow these steps to create a table for each corpus you want:

### Find and Download the Corpus's .sql File
Go to the "## Supported Legislation" table and click on the link of the requested corpus of legislation Download Link. This is a link to a hosted file storage system which will automatically initiate a download.



### Run the SQL File
There are different ways to run the SQL file. I recommend using psql.

#### Installing psql
Windows
Download and install PostgreSQL from the official website:
https://www.postgresql.org/download/windows/
During the installation process, make sure to check the box for installing psql.
Once the installation is complete, open the Command Prompt and type psql --version to verify the installation.
MacOS
Install PostgreSQL using Homebrew:
```sh
brew install postgresql
```
After installation, you can start the PostgreSQL service:
```sh
brew services start postgresql
```
Verify the installation by typing psql --version in your terminal.
Linux
Install PostgreSQL using your package manager. For example, on Ubuntu:
```sh
sudo apt update
sudo apt install postgresql postgresql-contrib
```
Switch to the postgres user and start the PostgreSQL prompt:
```sh
sudo -i -u postgres
psql
```
Verify the installation by typing psql --version.
#### Running the SQL File
Open Terminal or Command Prompt
Open your terminal or command prompt.

Navigate to the Directory Containing the .sql File
Use the cd command to navigate to the directory where your .sql file is located.
```sh
cd path/to/your/sql/file
```

Execute the following command to run your .sql file and connect it to your local PostgreSQL database:
```sh
psql -U your_username -d your_database -f country_jurisdiction_corpus.sql
```
Replace your_username with your PostgreSQL username, your_database with the name of your database, and your_file.sql with the name of your .sql file.

#### Example
Assuming your username is myuser, your database name is mydatabase, and your file is named us_az_statutes.sql, the command would be:
```sh
psql -U myuser -d mydatabase -f us_az_statutes.sql
```

This command will prompt you to enter your PostgreSQL password. After entering the password, it will execute the .sql file and populate your database with the data from the file.

By following these steps, you can successfully download and run the .sql files to create tables for each corpus you need in your PostgreSQL database.

## Running Scrapers Locally
Besides downloading data, this repository contains all of the source code on all supported corpus of legislation and the Python based scrapers which scraep, process, and clean the data. You are free to modify, use, and update these programs as you see fit. If you'd prefer to run them yourselves, which would allow for more regular updates, go for it! You can run these scrapers yourself by following these steps.

### Setup Instructions
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
   Ensure you have PostgresSQL installed and set up on your machine. Populate the database config file (**TODO**)

### Running Scrapers

To run an existing scraper for a specific jurisdiction (e.g., California statutes):

1. **Navigate to the Scraper Directory:**
   Going to the "## Supported Legislation" table, click on the corpus of choice's "Source Code" field. This will take you to the location of the specific scraper within the correct corpus, jurisdiction, and country folder.

2. **Run the Scraper:**
   Run the Python scraper normally.


### Python SDK
**TODO**
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/pydantic-model.png?raw=true">

### Typescript SDK
**TODO**

## About Our Schema
Populating knowledge graph

## Preparing Bulk Data for Usage with LLM
More here


## Democratizing Legal Knowledge for All

Our dream is to curate a platform and community dedicated to providing primary source legislation data in a unified and accessible format. Building applications in the legal field is difficult considering the incredible barriers to accessing legislation data in a standardized format for use with code. A legal engineer wanting to build an application which relies on primary source legislation would first need to spend considerable time and effort sourcing this legislative data before they could even begin to build. We want to remove these barriers, and provide instant and easy access so that our community can just start building. We believe legal data and law itself is a public good, and should be readily and easily accessible for all.


## Contributing

We welcome contributions from the community! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project, including how to add new jurisdictions.

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
