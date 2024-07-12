import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
import re
from bs4.element import Tag

import json

# Replacle with the state/country code
JURISDICTION = "il"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "madeline"
# Don't include last / in BASE_URL
BASE_URL = "https://www.ilga.gov/legislation/ilcs/"
ARTICLE_BASE_URL = "https://www.ilga.gov"
TOC_URL = "https://www.ilga.gov/legislation/ilcs/ilcs.asp"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["Repealed"]


def main():
    insert_jurisdiction_and_corpus_node()

    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="toplinks")
    link_container = soup.find("ul")
    hierarchy = []
    current_top_level = None


    current_element = link_container.find_all('div')

    for item in current_element:
    
        current_top_level = item.get_text(strip=True)
        chapters = item.find_next_siblings("li")
    
        for chapter in chapters:
            chapter_link = chapter.find('a')
            chapter_name = get_text_clean(chapter_link)
            chapter_name = re.sub(r'\s+', ' ', chapter_name)
            chapter_url = BASE_URL + chapter_link['href']
            scrape_per_chapter(chapter_url, chapter_name, current_top_level)

    
        for item in hierarchy:
            print(f"Top Level: {item['top_level']}")
            for link in item['links']:
                print(f" - {link}")
            break

        hierarchy = [] 
        current_top_level = None
        
    

def scrape_per_chapter(url, chapter_name, top_level_name):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    node_type = "structure"
    node_level_classifier = "CODE"
    node_name = top_level_name
    top_level_title = top_level_name.replace(" ", "_")
    node_link = TOC_URL
    og_parent = f"{JURISDICTION}/statutes/"
    node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    chapter_node_parent = node_id


    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_name = chapter_name
    node_number = chapter_name.split(" ")[1]
    node_link = url
    node_id = f"{chapter_node_parent}{node_level_classifier}={node_number}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, chapter_node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)

    act_node_parent = node_id

    
    link_container = soup.find("ul")
    hierarchy = []
    current_top_level = None


    current_element = link_container.find_all('li')

    for item in current_element:

        act_link = item.find('a')
        act_name = get_text_clean(act_link)
        act_url = BASE_URL + act_link['href']

        scrape_act(act_url, act_name, current_top_level, top_level_title, act_node_parent)


def scrape_act(url, act_name, current_top_level, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors='ignore') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")


    node_type = "structure"
    node_level_classifier = "ACT"
    node_name = act_name
    node_number= act_name.split(" ")[2].rstrip("/")
    node_id = f"{node_parent}{node_level_classifier}={node_number}/"
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    section_node_parent = node_id


   

    section_header = soup.find("div", class_="heading")
    section_container = section_header.find_next_sibling("p")
    if soup.find("div", class_="indent10") is not None:
        articles = soup.find_all("div", class_="indent10")

        for article in articles: 
            article_link = article.find("a")
            article_name = get_text_clean(article_link)
            article_url = ARTICLE_BASE_URL + article_link['href']
            scrape_article(article_url, article_name, top_level_title, section_node_parent)
    
    else:
        scrape_section(node_link, section_container, top_level_title, section_node_parent)


def scrape_article(url, article_name, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors='ignore') # a `str`;
    soup = BeautifulSoup(text, features="html.parser")

    node_type = "structure"
    node_level_classifier = "ARTICLE"
    node_name = article_name
    node_number = article_name.split(" ")[1]
    node_link = url
    node_id = f"{node_parent}{node_level_classifier}={node_number}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    section_node_parent = node_id

    section_header = soup.find("div", class_="heading")
    section_container = section_header.find_next_sibling("p")
    scrape_section(node_link, section_container, top_level_title, section_node_parent)



def scrape_section(url, section_container, top_level_title, section_node_parent):

    section_titles = section_container.find_all("title")

    if ("ARTICLE" in section_node_parent):
        skip_first = True
    else:
        skip_first = False

    for i, title in enumerate(section_titles):
        if i == 0 and skip_first:
            continue
        
        node_citation = get_text_clean(title)
   
        if ("ARTICLE" in section_node_parent):
            if ("-" in node_citation):
                node_number_clean = node_citation.split("-")[-1].rstrip(".")
            else: 
                node_number_clean = node_citation.split("/")[-1].rstrip(".")
        else:
            node_number_clean = node_citation.split("/")[-1].rstrip(".")
        node_type = "content"
        node_level_classifier = "SECTION"
        node_id = f"{section_node_parent}{node_level_classifier}={node_number_clean}"
        
        node_text_container = title.find_next("table")
        

        section_text = node_text_container.find_all("code")

        node_text = []
        node_addendum = None
        node_tags = {}

        for section in section_text:
            text = get_text_clean(section)
            node_text.append(text)
            


        clean_node_text = [item for item in node_text if item]
        node_tags['references'] = clean_node_text[1]
        node_addendum = clean_node_text[-1]
    
        if ("Source " not in node_addendum):
            node_addendum = clean_node_text[-2] + clean_node_text[-1]

        for item in clean_node_text:
            if 'Sec. ' in item:
                node_number = item  
                clean_node_text.remove(item)
            if 'Source: ' in item:
                node_addendum = item
                clean_node_text.remove(item)

            for word in RESERVED_KEYWORDS:
                if word in item:
                    node_type = "reserved"
                    break
        
        if node_tags == {}:
            node_tags = None
        if node_type == "reserved":
            clean_node_text = None
            node_addendum = None
            node_tags = None
        node_name = f"Section {node_number_clean}"
        node_link = url
        node_data = (node_id, top_level_title, node_type, node_level_classifier, clean_node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, section_node_parent, None, None, None, None, None)
        insert_node_allow_duplicate(node_data)






        










    #### Extract content_node information 
    # node_name = ""
    # node_number = ""
    # node_level_classifier = "SECTION"
    # node_link = ""
    # node_citation = ""

    # node_id = f"{node_parent}{node_level_classifier}={node_number}"
    # node_type = "content" # Default to content


    #### Checking if a node is reserved
    # for word in RESERVED_KEYWORDS:
    #     if word in node_name:
    #         node_type = "reserved"
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


    #### Construct node_tags, or set to None
    # if len(indentation) > 0:
    #     node_tags['indentation'] = indentation
    # if node_tags != {}:
    #     node_tags = json.dumps(node_tags)
    # else:
    #     node_tags = None

    #### Construct node_references, or set to None
    # if len(internal) > 0:
    #     node_references['internal'] = internal
    # if len(external) > 0:
    #     node_references['external'] = external
    # if node_references != {}:
    #     node_references = json.dumps(node_references)
    # else:
    #     node_references = None

    ### ADD A CONTENT NODE, allowing duplicates

    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # insert_node_allow_duplicate(node_data)
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        f"{JURISDICTION}/",
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
        f"{JURISDICTION}/statutes/",
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
        f"{JURISDICTION}/",
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
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    

    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text

if __name__ == "__main__":
    main()