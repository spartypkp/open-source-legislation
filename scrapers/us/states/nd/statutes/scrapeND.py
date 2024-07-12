import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
import re
from bs4.element import Tag
from pypdf import PdfReader
import requests
import tempfile
import requests
from io import BytesIO
import pyth
from striprtf.striprtf import rtf_to_text

import json
from io import BytesIO
import time
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

JURISDICTION = "nd"
 = "will"
TABLE_NAME = "nd_node"
BASE_URL = "https://www.ndlegis.gov"
TOC_URL = "https://www.ndlegis.gov/general-information/north-dakota-century-code/classic.html"
RESERVED_KEYWORDS = ["Reserved.", "Repealed by "]
SKIP_TITLE = 8

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            print(line)
            if i < SKIP_TITLE:
                continue
            
            scrape_per_title(line.strip())

def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors="ignore") # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    try:
        node_name_start = soup.find(class_="field-content").get_text().strip()
    except:
        return
    top_level_title = node_name_start.split(" ")[1]

    og_parent = "nd/statutes/"
    container = soup.find(class_="clearfix text-formatted field field--name-field-pwv-custom-content field--type-text-long field--label-hidden field__item")
    node_name_end = container.find("h3").get_text().strip()
    title_node_name = f"{node_name_start} {node_name_end}"
    title_node_type = "structure"
    title_node_level_classifier = "TITLE"

    title_node_link = url
    title_node_id = f"{og_parent}TITLE={top_level_title}/"
    node_data = (title_node_id, top_level_title, title_node_type, title_node_level_classifier, None, None, None, title_node_link, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)

    

    #print(container.prettify())
    table = container.find("table").tbody
    for i, chapter in enumerate(table.find_all("tr")):
        all_tds = chapter.find_all("td")
        chapter_container = all_tds[0]
        node_number = chapter_container.get_text().strip().split("-")[-1].strip()
        
       

        link_container = all_tds[1]
        link = link_container.find("a")
        if link is None:
            node_type = "reserved"
            node_link = url
        else:
            node_link = "https://www.ndlegis.gov/cencode/" + link['href']
            node_type = "structure"

        name_container = all_tds[2]
        node_name = name_container.get_text().strip()
        node_level_classifier = "CHAPTER"
        
        node_id = f"{title_node_id}CHAPTER={node_number}/"
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
        skip = insert_node_skip_duplicate(node_data)
        if skip:
            continue
        if node_type != "reserved":
            scrape_sections(node_link, top_level_title, node_id)


def scrape_sections(url, top_level_title, node_parent ):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    

    container = soup.find(class_="clearfix text-formatted field field--name-field-pwv-custom-content field--type-text-long field--label-hidden field__item")
    table = container.find("table").tbody
    #print(table.prettify())

    chapters_text = None
    chapters_text_split = None
    for i, section in enumerate(table.find_all("tr")):


        
        all_tds = section.find_all("td")
        link_container = all_tds[0]
        link = link_container.find("a")
        #print(link['href'])
        node_link = "https://www.ndlegis.gov/cencode/" + link['href']
        node_citation_raw = link_container.get_text().strip()
        node_number = node_citation_raw.split("-")[-1]

        name_container = all_tds[1]
        node_name = node_citation_raw + " " + name_container.get_text().strip()
        
        node_level_classifier = "SECTION"
        node_type = "content"
        node_id = f"{node_parent}SECTION={node_number}"
        node_citation = f"N.D.C.C. § {node_citation_raw}"

        # Get all the chapter text only once
        if i == 0:
            response = requests.get(node_link)
            pdf_memory = BytesIO(response.content)
            pdf = PdfReader(pdf_memory)

            # Extract text from the first page (as an example)
            chapters_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text().replace("Page No. ", "")
                chapters_text += text
            chapters_text_split = chapters_text.split("\n")

        # Find the index of the 2nd "-" in the node_citation_raw.
        index = find_2nd(node_citation_raw, "-")
        chapter_pattern = node_citation_raw[:index+1]
        
        
        node_text = None
        for i, chunk in enumerate(chapters_text_split):
            if node_citation_raw + ". " in chunk:
                node_text = [chapters_text_split[i]]
                continue
            if node_text:
                if chapter_pattern in chunk[0:16]:
                    break

                for word in RESERVED_KEYWORDS:
                    if word in chunk:
                        node_type = "reserved"
                        break
                node_text.append(chunk)
        
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None,None, None)
        insert_node_allow_duplicate(node_data)

                
        
            
        

        

        
        




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



def find_2nd(string, substring):
   return string.find(substring, string.find(substring) + 1)

if __name__ == "__main__":
    main()