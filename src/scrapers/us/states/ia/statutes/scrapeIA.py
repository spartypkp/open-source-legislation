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
from pypdf import PdfReader
import requests
import tempfile
import requests
from io import BytesIO
import pyth
from striprtf.striprtf import rtf_to_text
import time

import json

# Replacle with the state/country code
JURISDICTION = "ia"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will"
# Don't include last / in BASE_URL
TOC_URL = "https://www.legis.iowa.gov/law/iowaCode"
BASE_URL = "https://www.legis.iowa.gov"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["Reserved.", "Repealed by "]


def main():
    
    insert_jurisdiction_and_corpus_node()
    scrape_titles()
    
    

def scrape_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    og_parent = f"{JURISDICTION}/statutes/"

    titleTable = soup.find(id="iacList")
    all_titles = titleTable.tbody.find_all("tr")
    for i, tr in enumerate(all_titles):
        all_tds = tr.find_all("td")
        name_td = all_tds[0]
        node_name_raw = get_text_clean(name_td).split("(")
        node_name = node_name_raw[0].strip()
        top_level_title = node_name.split(" ")[1]
        node_descendants = "(" + node_name_raw[1].strip()
        node_tags = json.dumps({"descendants": node_descendants})
        
        node_link_container = tr.find("a")
        node_link = TOC_URL
        next_node_link = BASE_URL + node_link_container['href']
        node_type = "structure"
        node_level_classifier = "TITLE"
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"


        title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, node_tags)
        print(node_id)
        insert_node_ignore_duplicate(title_node_data)
        scrape_level(next_node_link, top_level_title, node_id)

    

def scrape_level(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    levelTable = soup.find(id="iacList")
    all_levels = levelTable.tbody.find_all("tr")
    for i, tr in enumerate(all_levels):
        all_tds = tr.find_all("td")
        name_td = all_tds[0]
        node_name = get_text_clean(name_td)
        node_level_classifier = node_name.split(" ")[0].upper()
        node_number = node_name.split(" ")[1]
        node_type = "structure"

        node_link = url
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        

        ### CREATE AND INSERT STRUCTURE NODE, if it's already there, skip it
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        node_skipped = insert_node_skip_duplicate(node_data)
        print("Node skipped: ", node_skipped)
        if node_skipped:
           continue  # Or return

        next_node_link = BASE_URL + all_tds[1].find("a")['href']
        try:
            scrape_sections(next_node_link, top_level_title, node_id)
        except Exception as e:
            print("Broke out of scrape_sections")
            print(e)
            time.sleep(5)
            pass


    #### Only continue scraping if node is not reserved
    # if node_type != "reserved":
    #     scrape_section(node_link, top_level_title, node_id)




def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    print("Inside scrape_sections")
    sectionTable = soup.find(id="iacList")
    all_levels = sectionTable.tbody.find_all("tr")
    for i, tr in enumerate(all_levels):
        used_rtf = True
        all_tds = tr.find_all("td")
        name_td = all_tds[0]
        node_name = get_text_clean(name_td)
        node_level_classifier = "SECTION"
        node_citation_raw = node_name.split(" ")[0]
        node_number = node_citation_raw.replace("§", "").split(".")[1]
        node_type = "content"
        node_link_container = all_tds[2].find("a")
        node_link = BASE_URL + node_link_container['href']

        node_citation = f"Iowa Code § {node_citation_raw}"

        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        print(f"Possible node_id: {node_id}")



        ### Checking if a node is reserved
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                node_type = "reserved"
                break

        if len(node_name.strip().split(" ")) == 1:
            print("Node name is only one word, setting to reserved")
            node_type = "reserved"
        ### Before getting node_text, initialize defaults
        node_addendum = None
        node_text = None
        node_tags = {}
        node_incoming_references = {}
        internal = []
        external = []
        indentation = [] # Optional

        ### Don't get node_text for reserved nodes
        if node_type != "reserved":
            node_text = []
            node_addendum = ""
            
            # Fetch the content
            
            response = requests.get(node_link)
            file_like_object = BytesIO(response.content)
            text = rtf_to_text(file_like_object.read().decode('utf-8')).replace('\xa0', ' ').replace('\r', ' ').strip()
            
            if "serverErrorMessage" in text:
                
                node_tags['Bad RTF Format'] = "Couldn't download section as RTF, had to use PDF instead."
                node_link = node_link.replace("rtf", "pdf")
                print("Server error for: ", node_link)
                response_new = requests.get(node_link)
                pdf_memory = BytesIO(response_new.content)
                pdf = PdfReader(pdf_memory)

                section_text = ""
                # Extract text from the first page (as an example)
                
                for i, page in enumerate(pdf.pages):
                
                    text = page.extract_text().replace("Page No. ", "")
                    text = text.replace('\n\n', '***')  # Replace double newlines with a single newline
                    text = text.replace('\n', ' ')  # Replace single newlines with a space
                    text = text.replace('***', '\n')  # Replace the triple newline with a single newline
                    # Cut off all text before the § character
                    text = text[text.find("§"):]
                    # Cut off all text before the first space
                    text = text[text.find(" "):]
                    text = text.replace(" . ", ". \n")
                    section_text += text.strip()
                
                node_text = section_text
                used_rtf = False
                
            

            
            for word in RESERVED_KEYWORDS:
                if word in text:
                    node_type = "reserved"
                    break
            if node_type != "reserved" and used_rtf:
                possible_node_text = text.split("\n")
                #print(possible_node_text)
                #print(possible_node_text)
                addendum_found = False
                actually_reserved = False
                for i, line in enumerate(possible_node_text):

                    if line.strip() == "":
                        continue
                    if i == 0:
                        
                        if actually_reserved:
                            node_addendum = None
                            node_text = None
                            break
                    if line[0] == "[" and line[-1] == "]":
                        #print("Addendum found")
                        node_addendum += line + "\n"
                        addendum_found = True
                        continue
                    if "Referred to in" in line:
                        #print("Referred to in found")
                        # Extract the text after "Referred to in"
                        ref_citations = line.split("Referred to in")[1].strip()
                        # Split the text by commas
                        ref_citations = ref_citations.split(",")
                        #print(f"Ref citations: {ref_citations}")
                        # Add each citation to the internal list
                        for citation in ref_citations:
                            internal.append({"citation": citation, "text": line})
                    
                    if addendum_found:
                        node_addendum += line + "\n"
                        continue

                    #print("Default case!")
                    node_text.append(line)
                if node_addendum == "":
                    node_addendum = node_text.pop()
            else:
                node_text = None
                node_addendum = None
            
                    
            




        ### Construct node_tags, or set to None
        if len(indentation) > 0:
            node_tags['indentation'] = indentation
        if node_tags != {}:
            node_tags = json.dumps(node_tags)
        else:
            node_tags = None

        ### Construct node_references, or set to None
        if len(internal) > 0:
            node_incoming_references['internal'] = internal
        if len(external) > 0:
            node_incoming_references['external'] = external
        if node_incoming_references != {}:
            node_incoming_references = json.dumps(node_incoming_references)
        else:
            node_incoming_references = None

        ## ADD A CONTENT NODE, allowing duplicates

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, node_incoming_references, node_tags)
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
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)

def insert_node_ignore_duplicate(row_data, verbose=True):
    try:
        util.insert_row_to_local_db(, TABLE_NAME, row_data)
    except psycopg2.errors.UniqueViolation as e:
        print(f"** Inside insert_node_ignore_duplicate, ignoring the error: {e}")
    return

def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, node_incoming_references, node_tags = row_data
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
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)
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
    return clean_text

if __name__ == "__main__":
    main()