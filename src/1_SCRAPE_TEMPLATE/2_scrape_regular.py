import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from utils.pydanticModels import NodeID, Node
import re
from bs4.element import Tag
from utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node

import json

# Replacle with the state/country code
COUNTRY = "us"
JURISDICTION = "state_code"
CORPUS = "document_name"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"


# Don't include last / in BASE_URL
TOC_URL = "Link to table of contents"
BASE_URL = "basic link"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["REPEALED"]


def main():
    corpus_node = insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_per_title(url)
    

def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    
    #title_node_data = Node(node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    #insert_node_ignore_duplicate(node_data)
    

def scrape_level(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    
    #### Checking if a node is reserved
    # node_type = "structure"
    # node_tags = {}
    # for word in RESERVED_KEYWORDS:
    #     if word in node_name:
    #         node_type = f"{structure}_reserved"
    #         node_tags['reserved_reason'] = word
    #         break



    #### CREATE AND INSERT STRUCTURE NODE, if it's already there, skip it

    # node_data = Node(node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    # node_skipped = insert_node_skip_duplicate(node_data)
    # if node_skipped:
    #    continue  # Or return


    #### Only continue scraping if node is not reserved
    # if node_type != "reserved":
    #     scrape_section(node_link, top_level_title, node_id)




def scrape_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")



    #### Extract content_node information 
    # node_name = ""
    # node_number = ""
    # node_level_classifier = "SECTION"
    # node_link = ""
    # node_citation = ""

    # node_id = f"{node_parent}{node_level_classifier}={node_number}"
    

    #### Checking if a content node is reserved
    # node_type = "content"
    # node_tags = {}
    # for word in RESERVED_KEYWORDS:
    #     if word in node_name:
    #         node_type = f"{structure}_reserved"
    #         node_tags['reserved_reason'] = word
    #         break


    #### Before getting node_text, initialize defaults
    # node_addendum = None
    # node_text = None
    # node_tags = {}
    # node_references = {}
    # internal = []
    # external = []
    # indentation = [] # Optional

    #### Don't get node_text for reserved nodes
    # if node_type != "reserved":
    #     node_text = []
    #     node_addendum = ""
    #     # Get node_text


    #### Construct node_tags
    # if len(indentation) > 0:
    #     node_tags['indentation'] = indentation
   
    #### Construct node_references
    # if len(internal) > 0:
    #     node_references['internal'] = internal
    # if len(external) > 0:
    #     node_references['external'] = external
    

    ### ADD A CONTENT NODE, allowing duplicates
    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # insert_node_allow_duplicate(node_data)
    



def get_text_clean(element, direct_children_only=False):
    '''
    Get text from BeautifulSoup element, clean it, and return it.
    element: BeautifulSoup element (Tag, NavigableString, etc.)
    direct_children_only: If True, only get the text from the direct children of the element
    '''
    if element is None:
        raise ValueError("==== Element is None in get_text_clean! ====")
    
    # Only allow the get_text() function if the element is a BS4 Tag
    if not isinstance(element, Tag):
        direct_children_only = True

    # Get all direct children text, the XML way
    if direct_children_only:
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    

    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)
    return clean_text

def debug_soup_to_file(soup, filename=""):
    with open(f"{DIR}/data/debug_soup{filename}.txt", "w") as write_file:
        write_file.write(soup.prettify())
    write_file.close()
    return

def remove_all_br_tags(soup, verbose=False):
    num_unwrapped = 0
    num_decomposed = 0
    for br in soup.find_all('br'):
        length = len(br.find_all(recursive=False))
        
        if length >= 1:
            num_unwrapped += 1
            br.unwrap()
            
        else:
            num_decomposed += 1
            br.decompose()
    if verbose:
        print(f"== Nuking <br> Tags ==\nUnwrapped: {num_unwrapped}\nDecomposed: {num_decomposed}\n=====================")
    soup.smooth()

if __name__ == "__main__":
    main()