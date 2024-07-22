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
JURISDICTION = "de"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://delcode.delaware.gov"
TOC_URL = "https://delcode.delaware.gov"
SKIP_TITLE = 0 
RESERVED_KEYWORDS = ["[Repealed", "[Expired", "[Reserved"]

# MOST OF THE TIME: ["TITLE", "PART", "CHAPTER", "SECTION"]
# Going to chapter will bring you to the sections page (sometimes part)

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_all_titles(corpus_node)

def scrape_all_titles(node_parent: Node):
    soup = get_url_as_soup(TOC_URL).find(id="content")
    

    all_title_containers = soup.find_all("a")
    
    for i, title_container in enumerate(all_title_containers):
        if i < SKIP_TITLE:
            continue
        # Skip the delaware constiution
        if i == 0:
            continue
        href = title_container['href'].strip()
        if "/index.html" not in href:
            continue
        
        
        node_name = title_container.get_text().strip()
        number = node_name.split(" ")[1]
        top_level_title = number
        level_classifier = "title"
        link = f"{BASE_URL}/{href}"
        node_type = "structure"
        parent = node_parent.node_id
        node_id = f"{node_parent.node_id}/{level_classifier}={number}"

        title_node = Node(
            id=node_id, 
            link=link,
            top_level_title=top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=parent
        )
        insert_node(title_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)

        recursive_scrape(title_node)

    

# Handles any generic structure node, routes sections to scrape_sections
def recursive_scrape(node_parent: Node):
    soup = get_url_as_soup(str(node_parent.link)).find(id="content")
    # Indicates page contains sections, send to section scrape function
    if soup.find(id="CodeBody"):
        scrape_sections(node_parent, soup)
    else:
        structure_node_containers = soup.find_all("div", class_="title-links")
        # Iterate over the container of the structure nodes
        for i, structure_container in enumerate(structure_node_containers):
            link_container = structure_container.find("a")
            href = link_container['href'].strip()
            
    
            link = href.replace("../","")
            link = f"{TOC_URL}/{link}"
            node_name = link_container.get_text().strip()
            level_classifier = node_name.split(" ")[0].lower()
            number = node_name.split(" ")[1]

            if number[-1] == ".":
                number=number[:-1]

            node_type = "structure"
            parent = node_parent.node_id
            top_level_title = node_parent.top_level_title

            status=None
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    status = word.lower()
                    break

            node_id = f"{parent}/{level_classifier}={number}"
            structure_node = Node(
                id=node_id, 
                link=link,
                top_level_title=top_level_title, 
                node_type=node_type, 
                level_classifier=level_classifier,
                number=number,
                node_name=node_name, 
                parent=node_parent.node_id,
                status=status
            )
            
            insert_node(structure_node, TABLE_NAME, debug_mode=True)
            recursive_scrape(structure_node)


def scrape_sections(node_parent: Node, soup: BeautifulSoup):
    # Scrape a section regularly
    
    section_containers = soup.find_all("div", class_="Section")

    for i, div in enumerate(section_containers):
        
        section_header = div.find("div", class_="SectionHead")
        node_name = section_header.get_text().strip()
        # Clean up super weird formatting
        node_name = node_name.replace("§", "")
        node_name = node_name.strip()
        node_name = f"§ {node_name}"
        
        # This is legacy code, I have no idea. Im not gonna touch it for now
        number = section_header['id']
        
        node_type = "content"
        level_classifier = "section"
       
        link = str(node_parent.link) + f"#{number}"

        number = number.replace(",", "-").rstrip(".")
        node_id = f"{node_parent.node_id}/{level_classifier}={number}"
        
        status = None
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                status = "reserved"
                break
        
        node_text = None
        citation = f"{node_parent.top_level_title} Del. C. § {number}"

        # Finding addendum
        addendum = None
        core_metadata = None
        
        if not status:
            node_text = NodeText()
            addendum = Addendum()
            addendum.history = AddendumType(type="history", text="")
            addendum_references = ReferenceHub()
            for element in div.find_all(recursive=False):
                # Skip the sectionHead
                if 'class' in element.attrs and element['class'][0] == "SectionHead":
                    continue
                
                # I want to remove all &nbsp; and &ensp; from the elements text
                temp = element.get_text().strip()
                text = temp.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').strip()
                text = re.sub(r'\s+', ' ', text)

                if text == "":
                    continue
                
                if element.name == "p":
                    node_text.add_paragraph(text=text)
                    continue
            
                # Assume any left over text without a <p> tag is the addendum
                addendum.history.text += text
                
                if element.name == "a":
                    addendum_references.references[element['href']] = Reference(text=text)
            
            if addendum_references.references == {}:
                addendum_references = None
            addendum.history.reference_hub = addendum_references
        if addendum and addendum.history.text == "":
            addendum = None
            
        section_node = Node(
            id=node_id, 
            link=link,
            citation=citation,
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=node_parent.node_id,
            status=status,
            node_text=node_text,
            addendum=addendum
        )
            
        insert_node(section_node, TABLE_NAME, debug_mode=True)

if __name__ == "__main__":
     main() 