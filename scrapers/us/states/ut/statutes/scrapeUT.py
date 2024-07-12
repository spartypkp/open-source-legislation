import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import json
from bs4.element import Tag

 = "madeline"
TABLE_NAME = "ut_node"
BASE_URL = "https://le.utah.gov/xcode/"
TOC_URL = "https://le.utah.gov/xcode/code.html"
SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
RESERVED_KEYWORDS = ["Repealed"]

# [TITLE, CHAPTER, SECTION]
# [TITLE, CHAPTER, PART, SECTION]

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            get_top_level_title = url.split("/")[4]
            top_level_title = get_top_level_title.split("Title")[-1]
            #print(url)
            #print(top_level_title)
            scrape_per_title(url, top_level_title, "ut/statutes/")
    

def scrape_per_title(url, top_level_title, node_parent):
    # Read the xml file for the current title
    with open(f"{DIR}/data/title{top_level_title}.xml", "r") as read_file:
        text = read_file.read()
    read_file.close()
    # Load the xml text into soup
    soup = BeautifulSoup(text, features="html.parser")

    title_container = soup.find("title")
    top_level_title = title_container['number']
    #print(top_level_title)
    node_name_end = title_container.catchline.get_text().strip()
    #print(f"From catchline: {node_name_end}")
    node_name = f"Title {top_level_title} - {node_name_end}"
    node_level_classifier = "TITLE"
    node_type = "structure"
    node_link = url
    node_id = f"{node_parent}TITLE={top_level_title}/"
    print(node_id)
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)

    insert_node_ignore_duplicate(node_data)

    scrape_level(title_container, node_link, top_level_title, node_id)


# Change url to level_container, XML element
def scrape_level(level_container, url, top_level_title, node_parent):
    
    for i, element in enumerate(level_container.find_all(recursive=False)):
        node_tags = {}
        # Ignore the catchline, effdate from the previous level
        if element.name == "catchline" or element.name == "effdate" or element.name == "enddate":
            if element.name != "catchline":
                node_tags[element.name] = get_text_clean(element)
            continue
        
        node_level_classifier = element.name.capitalize()
        # Handle the sections separately, don't continue recursion
        if node_level_classifier == "Section":
            scrape_section(element, url, top_level_title, node_parent)
            continue
        
       
        citation_node_number = element['number']
        node_number = citation_node_number.split("-")[-1]
        node_name_end = get_text_clean(element.catchline)
        
        # Capitalize the first letter of node_level_classifier

        node_name = f"{node_level_classifier} {node_number} - {node_name_end}"
        node_level_classifier = node_level_classifier.upper()
        
        node_type = "structure"
        # Try and construct the URL if possible
        # TITLE: https://le.utah.gov/xcode/Title38/38.html
        # CHAPTER: https://le.utah.gov/xcode/Title38/Chapter1A/38-1a.html
        # PART: https://le.utah.gov/xcode/Title38/Chapter1A/38-1a-P1.html
        # SECTION: https://le.utah.gov/xcode/Title38/Chapter1A/38-1a-S101.html
        # Looks like it is possible. Anything after the ? does not seem to be necessary
        if node_level_classifier == "CHAPTER":
            
            constructed = f"{BASE_URL}Title{top_level_title}/Chapter{node_number}/{top_level_title}-{node_number}.html"
        elif node_level_classifier == "PART":
            chapter_node_number = citation_node_number.split("-")[1]
            constructed = f"{BASE_URL}Title{top_level_title}/Chapter{chapter_node_number}/{top_level_title}-{chapter_node_number}-P{node_number}.html"
        #print(constructed)
        node_link = constructed
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        if node_tags != {}:
            node_tags = json.dumps(node_tags)
        else:
            node_tags = None
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                node_type = "reserved"
                break
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
        ### INSERT STRUCTURE NODE, if it's already there, skip it
        skip = insert_node_skip_duplicate(node_data)
        if skip:
            continue
    
        
        
        

        # Add the node
        
        # Check for reserved

        if node_type != "reserved":
            scrape_level(element, constructed, top_level_title, node_id)
        


def scrape_section(element, url, top_level_title, node_parent):
    #<section number="3-1-13">
    #
    node_level_classifier = "SECTION"
    node_type = "content"
    # U3-1-13
    
    node_citation_number = element['number']
    node_number = node_citation_number.split("-")[-1]
    node_name_end = element.catchline.get_text().strip()
    node_name = f"Section {node_number} - {node_name_end}"
    node_id = f"{node_parent}SECTION={node_number}"
   
    
    node_addendum = None
    if ("P" in url):
        constructed_url = url.split("P")[0]
        node_link = f"{constructed_url}S{node_number}.html"
        # print("this is nodelink with PART: " + node_link)
    else:
        constructed_url = url.replace(".html", f"-S{node_number}.html")
        node_link = constructed_url
        # print("this is node_link without part: " + node_link)
    node_citation = f"Utah Code Ann. § {node_citation_number}"


    constructed_url = f"{BASE_URL}Title{top_level_title}/{node_citation_number}.html"
    node_text = []
    indentation = []
    node_tags = {}
    node_references = {}
    internal = []
    external = []

    repealed_tag = element.find('enddate', {'type': 'RP'})
    if repealed_tag:
        node_tags['future_repealed'] = get_text_clean(repealed_tag)

    superseeded_tag = element.find('enddate', {'type': 'SC'})
    if superseeded_tag:
        node_tags['future_superseeded'] = get_text_clean(superseeded_tag)
    
    effective_tag = element.find('effdate')
    if effective_tag:
        node_tags['future_effective_date'] = get_text_clean(effective_tag)
   

    all_subsections = element.find_all(["subsection", "tab"], recursive=True)
    node_addendum = get_text_clean(element.histories)
    for subsection in all_subsections:
        # Handle the tab case
        print(subsection.prettify())
        print(subsection.name)
        if subsection.name == 'tab':
            if subsection.parent.name != "subsection" and subsection.parent.name != "section":
                print("BAD TAB case!")
                continue
            print("Tab case!")

            text = get_text_clean(subsection.next_sibling)
            if text:
                indentation.append("")
                node_text.append(text)
            continue

        # Default <subsection> 
        print("Default case!")
        text = get_text_clean(subsection, direct_children_only=True)
        node_text.append(text)
        subsection_indentation = subsection['number'].replace(node_citation_number, "")
        indentation.append(subsection_indentation)
        
        
        xrefs = subsection.find_all('xref')
        for xref in xrefs:
            # {"citation": "3-1-13(1)(c)"}
            internal.append({"citation": xref['refnumber']})

  
                
    node_tags['indentation'] = indentation
    node_tags = json.dumps(node_tags)
    
    if len(internal) > 0:
        node_references['internal'] = internal
    if len(external) > 0:
        node_references['external'] = external
    if node_references != {}:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    # Checking if a node is reserved
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            break
    
   

    ### FOR ADDING A CONTENT NODE, allowing duplicates
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_allow_duplicate(node_data)

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ut/",
        None,
        "jurisdiction",
        "STATE",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    corpus_row_data = (
        "ut/statutes/",
        None,
        "corpus",
        "CORPUS",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "ut/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)

def insert_node_ignore_duplicate(row_data, verbose=True):
    try:
        util.insert_row_to_local_db(, TABLE_NAME, row_data)
    except psycopg2.errors.UniqueViolation as e:
        if verbose:
            print(f"** Inside insert_node_ignore_duplicate, ignoring the error: {e}")
    return

def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, temp9, node_tags = row_data
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)

    base_node_id = node_id

    for i in range(2, 10):
        try:
            insert_node(node_data)
            if verbose:
                print(node_id)
            break
        except Exception as e:
            if verbose:
             print(f"** Inside insert_node_allow_duplicate, ignoring the error: {e}")
            node_id = base_node_id + f"-v{i}"
            if "structure" in node_type:
                node_id += "/"
                node_type = "structure_duplicate"
            elif "reserved" in node_type:
                node_type = "reserved_duplicate"
            else:
                node_type = "content_duplicate"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        continue

def insert_node_skip_duplicate(row_data, verbose=True):
    """
    Insert a node, but skip it if it already exists. Returns True if skipped, False if inserted.
    """
    node_id = row_data[0]
    try:
        insert_node(row_data)
        if verbose:
            print(node_id)
        return False
    except:
        if verbose:
            print("** Inside insert_node_skip_duplicate, skipping:",node_id)
        return True
    



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
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ').strip()
    
    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)
    return clean_text

    
if __name__ == "__main__":
    main()