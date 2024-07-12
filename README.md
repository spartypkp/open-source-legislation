# scraping-engine
Welcome to scraping-engine, a comprehensive Python-based solution designed for automating the extraction of legislative information from official .gov websites. 

How to Scrape A Jurisdiction

Key Terms We Made Up:
Top_level_title: The first explicit category used to split up legislation, always found as the first category on a main table of contents page. 
Reserved: This piece of legislation (structure or content node) can no longer be found here, because the legislature has decided to restructure/renumber/repeal it. 
Soup: The BeautifulSoup object in Python that contains the HTML of the entire current webpage.

Phase 0: Initial Research
Find the statutes web page
Find the Table of Contents page
This is where all the top_level_titles live
Find the first section and how i got there
Follow the path from top to bottom (usually this will be Title -> Chapter -> Section “links”)
What format is it in?
html
pdf
java
mixed?
choice for certain stages?
Repeat this for some random selections to get a good idea
Looking to understand the level hierarchy
Title -> Chapter ->  Section??
Always the same levels?
Always the same order?
Look to understand how the level hierarchy is displayed on the website.
Different html page for each level?
Maine is an example of when different levels occur on one page, versus a separate page for each level above chapter

Are there any helpful “expanded” views?
Look to generally understand the html of each level
What’s the name of the container for a level?
Are the elements of a level given unique IDs?
Is specific data like node_name or node_link specifically well named and tagged in the html elements?
Identify the language of node_name which means that the section is Reserved
Start a list of this, ex: “repealed, reserved, renumbered, “[ node_Name ]”...


Phase 1: Prepare Coding Environment
Find the country code/state code for the jurisdiction
Clone the SCRAPE_TEMPLATE directory
Rename readTEMPLATE, scrapeTEMPLATE, processTEMPLATE
In read, scrape, process, update global variables
the TABLE_NAME to “code_node” where code is the country/state code ex: “ca_node”
 to “will” “will2” or “madeline”
TOC_URL to the url of the table of contents
BASE_URL to the url truncated to remove all subpages
Create table in Postico

Phase 2: Read Top_level_titles (read.py)
Go to table of contents page where all top_level_titles live
Open read(STATE).py file 
Create data folder - empty
Complete more-in depth research about the TOC page
go to page and right-click inspect

find which HTML Element contains all top_level_title links, which themselves should be in html <a> tags


Make this HTML element the beautiful soup container
It’s set to be found by the id=, however you may have to use class_
Iterate over each top_level_title link
For each top level title_link, extract the actual link
Sometimes you have to add the BASE_URL + extracted href
Add it to the write_file (data/top_level_titles.txt)
If the next level page DOES NOT have the node_name or node_number information about the top_level_title, you may have to also store it on the top_level_titles.txt
I like storing the node name, which is usually the thing that’s missing if it is missing

Phase 2: Code Scraper (scrape.py)
Open scrape.py file 
Read in top level title from .txt folder in main()
Iterate over each line (each url)
Maybe iterate over each pairs of lines, if you included the url and the node_name
Research and define some properties of the legislation that will dictate which “method” of scraping we use
The levels for each top_level_title are constant
ALWAYS title -> chapter -> section
The ordering of levels between top_level_titles are constant
Changing order: 
TITLE=1 -> DIVISION -> PART -> SECTION
TITLE=4 -> PART -> DIVISION -> SECTION
Research some properties of the actual HTML structure, which will dictate which scraping method we use
Does each level have it’s own unique URL? Or are there multiple levels on the same page?
If unique, does the URL follow a predictable pattern that you could construct programmatically?
Ex: blah.gov/statutes/title=1/part=2/ ….
If there are multiple levels on the same page, you’re almost immediately ruling out the Iterative - Regular method
TODO
Choose which method we use
TODO 
DELETE the scrape file for the unused methods

Phase 2.1: Code Regular
Create a scrape function for each level
scrape_level(url, top_level_title, node_parent)
In each scrape function, create soup to find parent_container of the level elements
Iterate over each level element
Extract necessary node information for the level element
node_type is “structure” by default
“Content” for sections
Node_name needs to be scraped
It’s okay to include the node_number with the level name
Make sure to check for and handle weird formatting!!
&nbsp, other weird characters
Different versions of “-” or quotes
Check for reserved node_type by analyzing the node_name
node_level_classifier will always be NAME of level of function
Usually found from node_name
Node_number is the number or id of the node_level classifier
Related to node_name
create node_id for current level 
Don’t include trailing “/” for section level
Find the node_link for the current level element
IF the node_type is “Content”, extract the content specific information
Node_text
Node_addendum
Node_citation
Node_tags
node_references
Insert node, handling duplicates in some way
Duplicate “content” nodes are allowed, adding -v2 for duplicates
Duplicate “structure” nodes are generally not allowed, you’re going to want handle these in debugging
Call the next scrape function if needed

Phase 2.2: Code Recursive

Phase 2.3: Code Stack

Phase 3: Debug Scraper (scrape.py)
Add print statements for each level, printing out the node_id
Incrementally Test, add debug print and exit() after each stage
Start by trying to add the first top_level_title
Try to add each next structure_node level
Try to add the FIRST content_node
Try to add all of the FIRST content_nodes for the first structure_node
Let it cook
Watch for errors as they happen, fix them
Specific instructions TODO
At the start, when it’s cooking you need to do PERIODIC and thorough spot checks
Check everything looks good, common “MISSSED” errors
Not accurately tagging Reserved nodes
Node_link not working
Forgetting to add node_references/node_tags when you’re actually scraping them
Node_text is not weird
Node_citation is not fucked up
Node_parent CORRECTLY implemented
Phase 4: Process Database (process.py)
Run the scrape.py file, which will get the vector embeddings for all valid nodes
Run the query to update node_direct_children field ( SQL_QUERIES.txt)
Run the query to update node_siblings field (SQL_QUERIES.txt)

MAKE SURE that all fields are the right type
Common offenders include:
Node_text is NOT of type Vector(1536)
Node_tags, node_references is NOT jsonb
Optionally run other processing modules
Definition Extraction
Reference extraction
Other TBD


Phase 5: Upload to Cloud - PGADMIN
1- Connect to local database server 
2- right click on local database and backup 
3- In backup 

    General:
     -insert Filename
     -Format: select Directory
     -Rolename: select yourname

    Data Options:
     -Sections: select Data 
     -Do not save: select everything

    Skip:
     -Query Options, Table Options, Options

     Objects:
      -Select data table to backup 
      -Select Sequences

Click Backup & wait to complete

4-Disconnect local, connect to supabase -- postgres 
5-right click postgres and restore
6- In restore

        General:
         -Format: Directory
         -Filename: what you named Filename from backup
         -Rolename: postgres

        Data Options:
         -Sections: Data Options
         -Do not save: select everything


        Skip everything else

Click restore & wait to complete

Disconnect from supabase server


Recursive Methods:
	Easy: Michigan, Idaho, 
	Hard:USCode, ECFR, New Mexico
Regular: Montana, North Dakota, Nebraska, Ohio, West Virginia, AIM, New York
Stack: California, North Carolina


=======================================
Recursive Method

main()
scrape_per_title():
Get the top level title

scrape_structure()
Get the next level, no matter the name, following hierarchy
Only break out of this recursive function when you hit a section,
When done recursing, call scrape_section

scrape_section()
Get the section information
========================================
Iterative Method - Regular (Levels orders don’t change, always the same levels too)
** Always title -> chapter -> section

main()
scrape_per_title():
Get the top level title

scrape_chapter()
Get the chapter information

scrape_section() - page of ONE section
Get the section information

scrape_sections() - page of only sections
Get the section information for each

========================================

Iterative Method - Stack (Unordered List of Structure Nodes)
** All structure nodes are only on one page
** REQUIRES CONSTANT LEVEL ORDER at least the top_level_title
** Maybe they’re in a LIST of divs, flat

main()

scrape_per_title():
Get the top level title

LEVELS_ORDER = [“TITLE, CHAPTER, ARTICLE, SECTION”]
STACK = [TITLE 1, CHAPTER 2, ARTICLE 2]
scrape_structure()
Handle each div in the list, checking what depth the structure node should be
Use stacks data_structure

Get the section information

scrape_sections() - page of only sections
Get the section information for each

============================================

