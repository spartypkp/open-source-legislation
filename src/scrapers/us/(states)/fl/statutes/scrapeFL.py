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
JURISDICTION = "fl"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://www.flsenate.gov"
TOC_URL = "https://www.flsenate.gov/Laws/Statutes"
SKIP_TITLE = 0 
RESERVED_KEYWORDS = []


def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_all_titles(corpus_node)
    
def scrape_all_titles(node_parent: Node):

    soup = get_url_as_soup(TOC_URL)
    statutes_container = soup.find("div", class_="statutesTOC")
    all_title_containers = statutes_container.find_all("a")

    for i, title_container in enumerate(all_title_containers):
        if i < SKIP_TITLE:
            continue

        href = title_container["href"]
        link = f"{BASE_URL}/{href}"

        title_spans = title_container.find_all("span")
        number_span = title_spans[0]

        node_name = number_span.get_text()
        number = node_name.split(" ")[1]


        level_classifier = "title"

        description_span = title_spans[1]

        node_name += " " + description_span.get_text()

        chapter_span = title_spans[2]
        core_metadata = {"chapterRange": chapter_span.get_text()}
        node_type = "structure"

        parent = node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"
        print(node_id)
        if node_id == "us/fl/statutes/title=XXXIII":
            exit(1)
        else:
            continue
        title_node = Node(
            id=node_id, 
            link=link,
            top_level_title=number, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=parent,
            core_metadata=core_metadata
        )
        insert_node(title_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)
        scrape_chapters(title_node)


def scrape_chapters(node_parent: Node):
    soup = get_url_as_soup(str(node_parent.link))

    statutes_container = soup.find("div", class_="statutesTOC")

    chapter_parent = statutes_container.find("ol", class_="chapter")
    all_chapter_containers: List[Tag] = chapter_parent.find_all("a")
    

    for i, chapter_container in enumerate(all_chapter_containers):
        
        

        href = chapter_container["href"]
        link = f"{BASE_URL}/{href}"

        chapter_spans = chapter_container.find_all("span")
        
        number_span = chapter_spans[0]
        node_name = number_span.get_text().strip()
        
        
        number = node_name.split(" ")[1]
        
        level_classifier = "chapter"

        description_span = chapter_spans[1]

        node_name += " " + description_span.get_text().strip()

        
        node_type = "structure"

        parent = node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"

        chapter_node = Node(
            id=node_id, 
            link=link,
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=parent
            
        )
        insert_node(chapter_node, TABLE_NAME, debug_mode=True)

        possible_part_parent = chapter_container.parent.find("ol", class_="part")
        if possible_part_parent is not None:
            scrape_parts(chapter_node, possible_part_parent)
        else:
            

            find_section_links(chapter_node)


def scrape_parts(node_parent: Node, soup: BeautifulSoup):
    all_part_containers = soup.find_all("a")

    for i, part_container in enumerate(all_part_containers):
        href = part_container["href"]
        link = f"{BASE_URL}/{href}"

        part_spans = part_container.find_all("span")
        number_span = part_spans[0]

        node_name = number_span.get_text()
        number = node_name.split(" ")[1]

        level_classifier = "part"

        description_span = part_spans[1]

        node_name += " " + description_span.get_text()

        section_span = part_spans[2]
        core_metadata = {"sectionRange": section_span.get_text()}
        node_type = "structure"

        parent = node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"
        part_node = Node(
            id=node_id, 
            link=link,
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=parent,
            core_metadata=core_metadata
        )
        insert_node(part_node, TABLE_NAME, debug_mode=True)
        find_section_links(part_node)



def find_section_links(node_parent: Node):
    soup = get_url_as_soup(str(node_parent.link))
    
    section_parent = soup.find("div", class_="CatchlineIndex")

    all_section_containers = section_parent.find_all("a")

    for i, section_container in enumerate(all_section_containers):
        href = section_container['href']
        link = f"{BASE_URL}/{href}"
        
        scrape_section(node_parent, link)

def scrape_section(node_parent: Node, link: str):
    soup = get_url_as_soup(link)
    main_container = soup.find("div", id="main")
    section_container = main_container.find("div", class_="Section")
    
    number_container = section_container.find("span", class_="SectionNumber")
    number = number_container.get_text().strip()
    
    name_container = section_container.find("span", class_="CatchlineText")
    node_name = name_container.get_text().strip()

    node_name = number + " " + node_name
    node_type = "content"
    level_classifier="section"
    
    parent = node_parent.node_id
    node_id = f"{parent}/{level_classifier}={number}"
    citation = f"Fla. Stat. § {number}"
    
    text_container = section_container.find("span", class_="SectionBody")
    all_paragraph_containers = text_container.find_all(recursive=False)
    node_text = None
    addendum=None
    core_metadata=None

    status=None
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            status = "reserved"
            break

    if not status:
        node_text = NodeText()

        for i, paragraph_container in enumerate(all_paragraph_containers):
            text = paragraph_container.get_text().strip()
            node_text.add_paragraph(text=text)

        addendum = Addendum()
        addendum_container = section_container.find("div", class_="History")
        addendum_text = addendum_container.get_text().strip()
        addendum.history = AddendumType(type="history", text=addendum_text)

        # Find extra goodies
        note_container = section_container.find("div", class_="Note")
        if note_container:
            if core_metadata is None:
                core_metadata = {}
            core_metadata["Note"] = note_container.get_text().strip()

    
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