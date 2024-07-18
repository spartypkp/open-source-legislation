<img width="100%" height="200" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/banner-xl.png?raw=true">

# Open Sourcing the World's Legislation

Welcome to open-source-legislation, a project which aims to provide access to global primary source legislation for all. The heart of the project is a Python based platform of webscrapers, individually tailored for each jurisdiction and corpus of legislation. We provide the capability to run these scrapers yourself, and populate your own SQL database of cleaned and processed primary source legislation. 


<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/bulkdata.png?raw=true">


We propose a unified schema for representing legislation as a hierarchical graph of nodes which creates a rich knowledge graph for each jurisdiction, specifically designed for use with Large Language Models. Soon we will offer bulk data downloads for all primary source legislation, as well as Python and Typescript SDKs for immediate and easy usage.


## Supported Legislation
| Country | Jurisdiction | Corpus | Status | Last Updated | Link |
|---------|--------------|--------|--------|--------------|-----------|
| mhl | federal | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/mhl/federal/statutes) |
| us | ak | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ak/statutes) |
| us | al | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/al/statutes) |
| us | az | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/az/statutes) |
| us | ca | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ca/statutes) |
| us | co | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/co/statutes) |
| us | ct | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ct/statutes) |
| us | de | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/de/statutes) |
| us | federal | ecfr | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/ecfr) |
| us | federal | usc | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/usc) |
| us | federal | aim | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/federal/aim) |
| us | fl | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/fl/statutes) |
| us | hi | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/hi/statutes) |
| us | ia | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ia/statutes) |
| us | id | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/id/statutes) |
| us | il | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/il/statutes) |
| us | in | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/in/statutes) |
| us | ks | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ks/statutes) |
| us | ky | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ky/statutes) |
| us | la | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/la/statutes) |
| us | ma | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ma/statutes) |
| us | md | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/md/statutes) |
| us | me | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/me/statutes) |
| us | mi | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mi/statutes) |
| us | mn | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mn/statutes) |
| us | mo | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mo/statutes) |
| us | mt | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/mt/statutes) |
| us | nc | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nc/statutes) |
| us | nd | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nd/statutes) |
| us | ne | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ne/statutes) |
| us | nh | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nh/statutes) |
| us | nm | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/nm/statutes) |
| us | ny | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ny/statutes) |
| us | oh | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/oh/statutes) |
| us | or | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/or/statutes) |
| us | pa | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/pa/statutes) |
| us | ri | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ri/statutes) |
| us | sc | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sc/statutes) |
| us | sd | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/sd/statutes) |
| us | tx | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/tx/statutes) |
| us | ut | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/ut/statutes) |
| us | vt | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/vt/statutes) |
| us | wa | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wa/statutes) |
| us | wi | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wi/statutes) |
| us | wv | statutes | Refactoring | 2024-07-18T14:14:23.318085 | [view](https://github.com/spartypkp/open-source-legislation/blob/main/src/scrapers/us/(states)/wv/statutes) |

Legislation status tracked in real time.


## Democratizing Legal Knowledge for All

Our dream is to curate a platform and community dedicated to providing primary source legislation data in a unified and accessible format. Building applications in the legal field is difficult considering the incredible barriers to accessing legislation data in a standardized format for use with code. A legal engineer wanting to build an application which relies on primary source legislation would first need to spend considerable time and effort sourcing this legislative data before they could even begin to build. We want to remove these barriers, and provide instant and easy access so that our community can just start building. We believe legal data and law itself is a public good, and should be readily and easily accessible for all.

## Downloading Legislation Data 
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/sql-dump.png?raw=true">

We aim to provide data downloads of primary source legislation for every supported jurisdiction and corpus. Currently, every supported corpus of legislation has a corresponding .sql file available for download. Running this SQL file will create that corpus's corresponding PostgresSQL file using individual insert statements. Follow these steps to create a table for each corpus you want:

### Find the Corpus's Repository
Go to the "## Supported Legislation" table and click on the link of the requested corpus of legislation.

### Download the Corpus's .sql File
The .sql file lives directly under the corpus parent repository, with the filename {country}_{jurisdiction}_{corpus}.sql.
<img width="100%" height="100%" src="https://github.com/spartypkp/open-source-legislation/blob/main/public/corpus-filepath.png?raw=true">
Note: If you already cloned the repository locally, skip this step.

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
### #Running the SQL File
Open Terminal or Command Prompt
Open your terminal or command prompt.

Navigate to the Directory Containing the .sql File
Use the cd command to navigate to the directory where your .sql file is located.
```sh
cd path/to/your/sql/file
```

#### Run the SQL File Using psql
Execute the following command to run your .sql file and connect it to your local PostgreSQL database:
```sh
psql -U your_username -d your_database -f your_file.sql
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
