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

from src.utils.pydanticModels import NodeID, Node, Addendum, AddendumType, NodeText, Paragraph, ReferenceHub, Reference, DefinitionHub, Definition, IncorporatedTerms, ALLOWED_LEVELS
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup



SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "id"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://legislature.idaho.gov"
TOC_URL =  "https://legislature.idaho.gov/statutesrules/idstat/"
SKIP_TITLE = 40
RESERVED_KEYWORDS = []




# TITLE 41
def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_toc_page(corpus_node)

def scrape_toc_page(node_parent: Node):
    soup = get_url_as_soup(TOC_URL)
    # The first vc-column-inner-wrapper is for page banner
    statutes_container = soup.find_all("div", class_="vc-column-innner-wrapper")[1]
    

    all_title_containers: List[Tag] = statutes_container.find_all("tr")
    for i, title_container in enumerate(all_title_containers):

        if i < SKIP_TITLE:
            continue

        td_list = title_container.find_all("td")
        node_name = td_list[0].get_text().strip()
        level_classifier="title"
        node_type="structure"
        number = node_name.split(" ")[1]

        node_name += " " + td_list[1].get_text().strip()
        link_container = title_container.find("a")
        href = link_container['href']
        link = f"{BASE_URL}{href}"
        parent=node_parent.node_id
        node_id=f"{parent}/title={number}"


        title_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=number,
            parent=parent
        )
        insert_node(title_node, TABLE_NAME, debug_mode=True)

        recursive_scrape(title_node)





def recursive_scrape(node_parent: Node):
    
    soup = get_url_as_soup(str(node_parent.link))


    # The first vc-column-inner-wrapper is for page banner
    table_container = soup.find_all("div", class_="vc-column-innner-wrapper")[1]
    
    rows = table_container.find_all("tr")
    for i, row in enumerate(rows):
        all_tds = row.find_all("td")
        link_container = all_tds[0].find("a")
        status=None
        try:
            
            link  = BASE_URL + link_container['href']
            node_type = "structure"
        except:
            link = str(node_parent.link)
            status = "reserved"

       
        if  "SECT" in link and status is None:
            node_name = link_container.get_text().strip() + " " + all_tds[2].get_text().strip()
            #print(node_name)
            number = node_name.split(" ")[0]
            number = number.split("-")[-1]
            #print(node_number)
            level_classifier = "section"
            parent=node_parent.node_id
            node_id = f"{parent}/{level_classifier}={number}"
            node_type = "content"
            citation = f"I.C. {node_parent.top_level_title} § {number}"
            section_node = Node(
                id=node_id,
                link=link,
                citation=citation,
                number=number,
                node_type=node_type,
                node_name=node_name,
                level_classifier=level_classifier,
                top_level_title=node_parent.top_level_title,
                parent=parent
                
            )

            scrape_section(section_node)
            continue
        
        
        try:
            node_name_start  = link_container.get_text()
            level_classifier = node_name_start.split(" ")[0].lower()
            # Found broken parts of the site: https://legislature.idaho.gov/statutesrules/idstat/Title41/T41CH35/
            if level_classifier.strip() == "":
                raise ValueError(f"Stupid Idaho broke this particular page: {link}")
            # Handle weird cases. See us/id/statutes/title=40/chapter=16, considering this an article
            if level_classifier not in ALLOWED_LEVELS:
                level_classifier = "article"
                number = node_name_start
            else:
                number  = node_name_start.split(" ")[1]
                number = number.replace(".","")
            if "[" in node_name_start and "]" in node_name_start:
                # Set the node number to the number in the brackets
                number = node_name_start.split("[")[1].split("]")[0]

        except:
            continue

        name_container = all_tds[2]
        node_name_end  = name_container.get_text()
        node_name = node_name_start + " " + node_name_end
        parent=node_parent.node_id
        
        if "REDESIGNATED" in node_name:
            status = "reserved"

        node_id = f"{parent}/{level_classifier}={number}"
        
        structure_node = Node(
                id=node_id,
                status=status,
                link=link,
                number=number,
                node_type=node_type,
                node_name=node_name,
                level_classifier=level_classifier,
                top_level_title=node_parent.top_level_title,
                parent=parent
                
            )
        
        insert_node(structure_node, TABLE_NAME, debug_mode=True)
        if not status:
            recursive_scrape(structure_node)

def scrape_section(current_node: Node):

    soup = get_url_as_soup(str(current_node.link))
    container = soup.find(class_="pgbrk")

    node_text = NodeText()

    addendum = Addendum(history=AddendumType(type="history",text=""))
    found_addendum = False
    
    for i, div in enumerate(container.find_all("div")):
        # Skip divs containing Title and Chapter headings
        if i < 4:
            continue
        
        txt = div.get_text().strip()
        
        if found_addendum or "History:" in txt:

            found_addendum = True
            addendum.history.text += txt
        else:
            node_text.add_paragraph(text=txt)

    current_node.node_text = node_text
    current_node.addendum = addendum
    insert_node(current_node, TABLE_NAME, debug_mode=True)
                    

if __name__ == "__main__":
    main()