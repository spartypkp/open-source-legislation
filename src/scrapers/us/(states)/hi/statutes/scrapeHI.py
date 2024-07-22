import os
import sys
# BeautifulSoup imports
from bs4 import BeautifulSoup
from bs4.element import Tag

# Selenium imports
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from typing import List, Tuple
import time
import json
import re

from pathlib import Path

DIR = os.path.dirname(os.path.realpath(__file__))
# Get the current file's directory
current_file = Path(__file__).resolve()

# Find the 'src' directory
src_directory = current_file.parent
while src_directory.name != 'src' and src_directory.parent != src_directory:
    src_directory = src_directory.parent

# Get the parent directory of 'src'
project_root = src_directory.parent

# Add the project root to sys.path
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils.pydanticModels import NodeID, Node, Addendum, AddendumType, NodeText, Paragraph, ReferenceHub, Reference, DefinitionHub, Definition, IncorporatedTerms
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup



SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "hi"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
TOC_URL = "https://www.capitol.hawaii.gov/docs/hrs.htm"
BASE_URL = "https://www.capitol.hawaii.gov"
SKIP_TITLE = 0 
RESERVED_KEYWORDS = ["REPEALED", "Repealed"]
DRIVER = None



def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_toc_page(corpus_node)
    
def scrape_toc_page(node_parent: Node):
    global DRIVER
    # Use Selenium in headless mode
    # chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)


    soup = BeautifulSoup(DRIVER.page_source, features="html.parser")

    all_structure_node_containers = soup.find_all("a")
    for i, structure_node_container in enumerate(all_structure_node_containers):
        if i > 100:
            exit(1)
        node_name = structure_node_container.get_text().strip()
        level_classifier = node_name.split(" ")[0].strip().lower()
        
        if (level_classifier == "division" or level_classifier == "title"):
            continue
        href = structure_node_container['href']
        scrape_chapter(node_parent, href)
        
    
    

def scrape_chapter(node_parent: Node, url: str):
    chapter_driver = webdriver.Chrome()
    chapter_driver.get(url)

   
    soup = BeautifulSoup(chapter_driver.page_source, features="html.parser")

    

    structure_containers = soup.find_all("p", attrs={"align": "center"})

    node_type="structure"
    link=url
    
    

    for i, structure_container in enumerate(structure_containers):
        node_name = structure_container.get_text().strip()
        print(node_name)
        if "DIVISION" in node_name:
            level_classifier = "division"
            number_text = node_name.replace("DIVISION","").strip()
            number = number_text.split(" ")[0]
            number=number.rstrip(".")
            division_parent=node_parent.node_id
            division_node_id = f"{division_parent}/division={number}"
            division_node = Node(
                id=division_node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=number,
                parent=division_parent
            )
            insert_node(division_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)
            node_parent=division_node
        elif "TITLE" in node_name:
            level_classifier="title"
            number_text = node_name.replace("TITLE","").strip()
            number = number_text.split(" ")[0]
            number=number.rstrip(".")
            title_parent=node_parent.node_id
            title_node_id = f"{title_parent}/title={number}"
            title_node = Node(
                id=title_node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=node_parent.top_level_title,
                parent=title_parent
            )
            insert_node(title_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)
            node_parent=title_node
        elif "CHAPTER" in node_name:
            level_classifier="chapter"
            number_text = node_name.replace("CHAPTER","").strip()
            number = number_text.split(" ")[0]
            number=number.rstrip(".")
            chapter_parent=node_parent.node_id
            chapter_node_id = f"{chapter_parent}/chapter={number}"
            chapter_node = Node(
                id=chapter_node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=node_parent.top_level_title,
                parent=chapter_parent
            )
           
            node_parent=chapter_node
        else:
            if node_name == "":
                continue

            if node_parent.level_classifier == "chapter":
                node_parent.node_name += " " + node_name
            
    insert_node(chapter_node, TABLE_NAME,  debug_mode=True)  

        
    all_section_links = soup.find_all("a")
    for i, a_tag in enumerate(all_section_links):
        a_tag_text = a_tag.get_text().strip()
        if "-" not in a_tag_text:
            continue
        href=f"{BASE_URL}{a_tag['href']}"
        scrape_section(href, chapter_node)



# Division 1. Government
# 1 - 21
# Division 2. Business
# 22 - 27
# Division 3. Property; Family
# 28 - 31
# Division 4. Courts and Judicial Proceedings
# 32 - 36
# Division 5. Crimes and Criminal Proceedings
# 37 - 41


def scrape_section(url: str, node_parent: Node):
    section_driver = webdriver.Chrome()
    section_driver.get(url)
    
    
    soup = BeautifulSoup(section_driver.page_source, features="html.parser")

    node_type = "content"
    node_level_classifier = "section"

    # Before getting node_text, initialize defaults
    node_addendum = None
    node_text = None
    core_metadata = None


    all_a_tags = soup.find_all("a")
    for a_tag in all_a_tags:
        if 'href' in a_tag.attrs:
            href = a_tag['href']
            if href == 'https://www.capitol.hawaii.gov/help.aspx':
                return
    # Don't get node_text for reserved nodes
    all_p_tags = soup.find_all("p")
    category = None
    #print(len(all_p_tags))
    empty_node_name = True
    #print("=== Inside scrape section enumerate === \n")
    for i, p in enumerate(all_p_tags):
        txt = get_text_clean(p)
        
        #print(f"i: {i}, txt: {txt}")
        if txt == "":
            continue
        if "PART " in txt[0:10]:
            continue

        if p.find("b") and empty_node_name:
            #print("Found bold")
            bold = p.find("b")
            print(f"bold: {bold}")

            node_name = txt
            # if len(p.find_all("b")) > 1:
            #     node_name += get_text_clean(bold.next_sibling) + " "
            #     print(node_name)
            #     node_name += get_text_clean(p.find_all("b")[-1]) 
            #     print(node_name)
            
            node_name = node_name.replace("[", "").replace("]", "").strip()
            node_name = node_name.replace("- ", "-")
            print(f"replaced node_name: {node_name}")
            last_b = p.find_all("b")[-1]
            if get_text_clean(last_b) == "":
                last_b = bold
            # Extract the last word in the last b tag
            last_b_text = get_text_clean(last_b).replace("[", "").replace("]", "").replace("- ", "-").strip()
            print(f"last_b_text: {last_b_text}")
            last_b_last_word = last_b_text.split(" ")[-1]
            print(f"last_b_last_word: {last_b_last_word}")

            # Find the index of last_b_last_word in node_name
            index = node_name.find(last_b_last_word)
            print(f"Index of last_b_last_word: {index}")
            # Remove everything after index+len(last_b)
            node_name = node_name[:index+len(last_b_last_word)]
            #print(f"node_name: {node_name}")
            node_citation = node_name.split(" ")[0]

            node_number = node_citation.split("-")[-1]
            #print(f"node_number: {node_number}")
            empty_node_name = False
            #### Checking if a node is reserved
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved"
                    break
            if node_type == "reserved":
                break
    
        
        
        for a_tag in p.find_all("a"):
            if 'href' not in a_tag.attrs:
                continue
            href = a_tag['href']
            ref_url = url + "#" + href
            internal.append({"citation": href, "link": ref_url, "text": txt})
        
        #print(p.attrs)
        if p['class'][0] == "XNotesHeading":
            category = txt
        elif p['class'][0] == "XNotes":
            if category not in node_tags:
                node_tags[category] = []
            node_tags[category].append(txt)
        else:
            node_text.append(txt)

    node_id = f"{node_parent}SECTION={node_number}"
    node_citation = f"HRS {node_citation}"
    node_link = url
    # Find any text within [ and ] in node_text[-1]
    node_addendum = None
    if node_text and "[" in node_text[-1] and "]" in node_text[-1]:
        node_addendum = node_text[-1].split("[")[1].split("]")[0]
        

     # Construct node_tags, or set to None
    if len(indentation) > 0:
        node_tags['indentation'] = indentation
    if node_tags != {}:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None

    # Construct node_references, or set to None
    if len(internal) > 0:
        node_references['internal'] = internal
    if len(external) > 0:
        node_references['external'] = external
    if node_references != {}:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    if len(node_text) == 0:
        node_text = None

    
    ### FOR ADDING A CONTENT NODE, allowing duplicates
    node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_allow_duplicate(node_data)


    





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
