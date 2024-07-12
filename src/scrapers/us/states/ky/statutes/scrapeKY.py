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
from node import Node
import json
from pypdf import PdfReader
import requests

from io import BytesIO

# Replacle with the state/country code
JURISDICTION = "ky"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will"
# Don't include last / in BASE_URL
BASE_URL = "https://apps.legislature.ky.gov"
TOC_URL = "https://apps.legislature.ky.gov/law/statutes/"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["Repealed,", "Not yet utilized", "Superseded"]
# "Not yet utilized", "Superseded"


def main():
    insert_jurisdiction_and_corpus_node()
    scrape_titles()
    



def scrape_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="lxml")

    og_parent = "ky/statutes/"
    
    

    title_schema = ["TITLE", "CHAPTER", "SUBTITLE", "SUBCHAPTER", "ARTICLE"]

    
    titles_container = soup.find(id="Panel1")
    
    remove_all_br_tags(titles_container)
    

    
    for i, element in enumerate(titles_container.find_all(id="title")):
        
        
        node_name = get_text_clean(element)
        top_level_title = node_name.split(" ")[1].strip()
        node_level_classifier = "TITLE"
        node_type = "structure"
        node_link = TOC_URL
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"

        current_node = Node(node_id, og_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
        title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_skip_duplicate(title_node_data)

        # Find the ul container
        parent = element.parent
        
        next_level_container = parent.next_sibling

        scrape_levels(next_level_container, top_level_title, current_node)



def scrape_levels(level_container, top_level_title, node_parent):
    current_node = node_parent
    title_schema = ["TITLE", "CHAPTER", "SUBTITLE", "SUBCHAPTER", "ARTICLE"]


    for element in level_container.find_all("li"):

        node_name = get_text_clean(element)
        node_number = node_name.split(" ")[1].strip()
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        
        node_level_classifier = node_name.split(" ")[0].upper()


        # Make plural classifiers into singular
        if node_level_classifier[-1] == "S":
            node_level_classifier = node_level_classifier[:-1]
        try:
            node_link = TOC_URL + element.find("a")['href']
        except:
            node_link = TOC_URL
        
        node_type = "structure"
        node_tags = {}

    
        # Handle all content nodes first
        
        
        currentRank = title_schema.index(current_node.node_level_classifier)
        #print(f"Current: {currentRank}")
        
        newRank = title_schema.index(node_level_classifier)
        #print(f"New: {newRank}")
        
    
                # Determine the position of the newNode in the hierarchy
        if (newRank <= currentRank):
            temp_node = current_node

            while (title_schema.index(temp_node.node_level_classifier) > newRank):
                temp_node = temp_node.node_parent
                if (temp_node.node_level_classifier == 'TITLE'):
                    break
                
            
            current_node = temp_node
            currentRank = title_schema.index(current_node.node_level_classifier)
            # Set the ID of the newNode and add it to the current_node's children or siblings
            if (newRank == currentRank):
                if (not current_node.node_parent):
                    print("current_node.parent undefined!")
                    exit(1)

            
                node_parent = current_node.node_parent
                node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
                
                
                
                
                current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
            else:
                
                node_parent = current_node
                node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
                
                current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
            

            
        else:
            # Set the ID of the newNode and add it to the current_node's children
            node_id = f"{current_node.node_id}{node_level_classifier}={node_number}/"
            
            node_parent = current_node
            current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
        
        
        
        node_tags = {}
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                current_node.node_type = f"structure_reserved"
                temp_node_tags = current_node.node_tags
                if temp_node_tags is None:
                    temp_node_tags = {}
                temp_node_tags['reserved_reason'] = word
                current_node.node_tags = temp_node_tags
                break

        
        current_node_data = current_node.get()
        skip = insert_node_skip_duplicate(current_node_data)
        
        if skip:
            continue
        if "reserved" not in current_node.node_type:
            scrape_sections(node_link, top_level_title, node_id)

    
    

def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    
    if soup.find(id="empty_text") is not None:
        return
    
    sections_container = soup.find(id="Panel1").find("span")
   
    
    remove_all_br_tags(sections_container)
    current_part = node_parent
    for element in sections_container.find_all(recursive=False):
        #print(element.name)
        if element.name == "div":
            node_name = get_text_clean(element)
            node_level_classifier = node_name.split(" ")[0].upper()
            if node_level_classifier != "PART":
                node_level_classifier = "CATEGORY"
                node_id = f"{node_parent}{node_level_classifier}={node_name.replace(' ', '-')}/"
            else:
                node_number = node_name.split(" ")[1].strip()
                node_id = f"{node_parent}{node_level_classifier}={node_number}/"
            node_link = url
            node_type = "structure"
            
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node_skip_duplicate(node_data)
            current_part = node_id
        elif element.name == "ul":
            all_a_tags = element.find_all("a")
            for i, a_tag in enumerate(all_a_tags):
                #print(i)
                #print(get_text_clean(a_tag))
                try:
                    link = "https://apps.legislature.ky.gov/law/statutes/" + a_tag['href']
                    scrape_section(link, top_level_title, current_part)
                except Exception as e:
                    print("Exception!", e)
                    link = url


def scrape_section(url, top_level_title, node_parent):
    
    response_new = requests.get(url)
    pdf_memory = BytesIO(response_new.content)
    pdf = PdfReader(pdf_memory)

    text = ""
    # Extract text from the first page (as an example)
    for i, page in enumerate(pdf.pages):
        txt = page.extract_text().replace("Page No. ", "")
        text += txt

    #print(text)
    all_text = text.split("\n")
    for i, line in enumerate(all_text):
        #print(i, line)
        # node_name case
        if i == 0:
            node_name = line
            node_citation_raw = node_name.split(" ")[0].strip()
            node_level_classifier = "SECTION"
            node_link = url
            node_type = "content"
            node_number = node_citation_raw.split(".")[1]
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            
            node_citation = f"KRS § {node_citation_raw}"
            node_tags = {}
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = f"content_reserved"
                    node_tags['reserved_reason'] = word
                    break

            
            node_text = []
            node_addendum = ""
            node_tags = {}
            node_references = {}

        if "Effective: " in line:
            node_tags['effective_date'] = line.split("Effective:")[1].strip()
        elif "History: " in line:
            node_addendum += line.split("History:")[1].strip()
        else:
            node_text.append(line)
            
                
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_allow_duplicate(node_data)

    
    
    

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
    insert_node_skip_duplicate(jurisdiction_row_data)
    insert_node_skip_duplicate(corpus_row_data)



def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, node_incoming_references, node_tags = row_data
    
    if node_references is not None and node_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None
    if node_incoming_references is not None and node_incoming_references:
        node_incoming_references = json.dumps(node_incoming_references)
    else:
        node_incoming_references = None

    if node_tags is not None and node_tags:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None
    
    
    if node_text is not None and node_text == []:
        node_text = None
    if node_addendum is not None and node_addendum == "":
        node_addendum = None
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)

    
    
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
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, node_incoming_references, node_tags = row_data
    
    if node_references is not None and node_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None
    
    if node_incoming_references is not None and node_incoming_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    if node_tags is not None and node_tags:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None
    
    if node_text is not None and node_text:
        node_text = None
    if node_addendum is not None and node_addendum:
        node_addendum = None
        
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)



    try:
        insert_node(node_data)
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