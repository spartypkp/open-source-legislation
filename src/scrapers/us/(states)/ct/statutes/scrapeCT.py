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
JURISDICTION = "ct"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://www.cga.ct.gov"
TOC_URL = "https://www.cga.ct.gov/current/pub/titles.htm"
SKIP_TITLE = 0 
RESERVED_KEYWORDS = []

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_titles(corpus_node)

def scrape_titles(node_parent: Node):
     
    
    soup = get_url_as_soup(TOC_URL)

    soup = soup.find(id="titles.htm")
    all_links = soup.find_all(class_="left_38pct")

    
    for title in all_links:
        link_container = title.find("a")
        name_container = title.next_sibling.next_sibling
        status=None
        try:
            node_name_start = link_container.get_text().strip()
            link = "https://www.cga.ct.gov/current/pub/" + link_container['href'] + "\n"
            node_name_end = name_container.find("a").get_text()
            
        except:
            node_name_start = title.find(class_="toc_ttl_desig").get_text().strip()
            node_name_end = name_container.find(class_="toc_ttl_name").get_text().strip()
            status = "reserved"
            link = TOC_URL

        top_level_title = node_name_start.split(" ")[1]
        number = top_level_title
        node_descendants = title.find(class_="toc_rng_chaps").get_text().strip()
        
        
        level_classifier = "title"
        node_type = "structure"
        node_id = f"{node_parent.node_id}/{level_classifier}={top_level_title}"
        node_name = f"{node_name_start} {node_name_end}"
        
        core_metadata = {}
        core_metadata["children_information"] = node_descendants


        title_node = Node(
            id=node_id, 
            link=link,
            top_level_title=top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=node_parent.node_id,
            core_metadata=core_metadata,
            status=status
        )
        insert_node(title_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)
        if not status:
            scrape_chapters(title_node)

            
    

def scrape_chapters(node_parent: Node):
    
    soup = get_url_as_soup(node_parent.link)
    #### Extract structure_node information from the url
    for i, chapter in enumerate(soup.find_all(class_="left_40pct")):
        link_container = chapter.find("a")
        status = None
        try:
            node_name_start = link_container.get_text().strip()
        except:
            # Last chapter found, return
            return
            
        number = node_name_start.split(" ")[1]
        link = "https://www.cga.ct.gov/current/pub/" + link_container['href'] + "\n"
        node_descendants = chapter.find(class_="toc_rng_secs").get_text().strip()
        name_container = chapter.next_sibling.next_sibling
        node_name_end = name_container.find("a").get_text()
        level_classifier = "chapter"
        node_type = "structure"
        node_name = f"{node_name_start} {node_name_end}"
        core_metadata = {}
        core_metadata["children_information"] = node_descendants
        node_id = f"{node_parent.node_id}/{level_classifier}={number}"

        chapter_node = Node(
            id=node_id, 
            link=link,
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            level_classifier=level_classifier,
            number=number,
            node_name=node_name, 
            parent=node_parent.node_id,
            core_metadata=core_metadata,
            status=status
        )
        insert_node(chapter_node, TABLE_NAME, debug_mode=True)
       
        if not status:
            scrape_sections(chapter_node)
        
def scrape_sections(node_parent: Node):
    
    soup = get_url_as_soup(node_parent.link)
    while True:
        br_tag = soup.find("br", recursive=False)
        if br_tag is None:
            break
        br_tag.decompose()
        


    for i, section in enumerate(soup.find_all(class_="toc_catchln")):
        link_container = section.find("a")

        

        node_sec_id = link_container['href'].replace("#","")
        number = node_sec_id.split("-")[-1]
        link = str(node_parent.link) + link_container['href']
       
        node_name = link_container.get_text().strip()
        level_classifier = "section"
        node_type = "content"

        status = None
        if section.find("b") is not None:
            status = "reserved"

        node_id = f"{node_parent.node_id}/{level_classifier}={number}"

        node_text = None
        addendum = None
        citation = f"Conn. Gen. Stat. § {node_parent.top_level_title}-{number}"
        core_metadata = None
        
        # Don't scrape text of reserved sections
        if not status:
            node_text = NodeText()
            addendum = Addendum()
            core_metadata = {}
            annotations = []

            iterator = soup.find(id=f"{node_sec_id}").parent
            while iterator:
                
                
                # Possibly ignoring tables here?
                if iterator.name == "table" and 'class' in iterator.attrs and iterator['class'][0] == "nav_tbl":
                    break

                txt = iterator.get_text().strip()
                # No matter what, skip all empty text elements
                if txt == "":
                    iterator = iterator.next_sibling.next_sibling
                    continue

                # Handle non-p tags
                if iterator.name != "p":
                    node_text.add_paragraph(txt)  
                    iterator = iterator.next_sibling.next_sibling
                    continue

                # Extract all references if they exist
                paragraph_references = ReferenceHub()

                for sec_link in iterator.find_all("a"):
                    cit = sec_link.get_text().strip()
                    lnk = "https://www.cga.ct.gov/current/pub/" + sec_link['href']
                    if "#" in lnk:
                        reference = Reference(text=cit)
                    else:
                        reference = Reference(text=cit)
                    
                    paragraph_references.references[lnk] = reference

                if paragraph_references.references == {}:
                    paragraph_references = None
                
                # Regular text
                if 'class' not in iterator.attrs:
                    node_text.add_paragraph(text=txt, reference_hub=paragraph_references)
                else:
                    # Add addendums for source, history, if they exist
                    
                    if iterator['class'][0] == "source-first":
                        addendum.source = AddendumType(type="source", text=txt, reference_hub=paragraph_references)
                    elif iterator['class'][0] == "history-first":
                        addendum.source = AddendumType(type="history", text=txt, reference_hub=paragraph_references)
                    else:
                        annotations.append(txt)
                
                if iterator.next_sibling.next_sibling.name == "None" or iterator.next_sibling.next_sibling.name is None:
                    iterator = iterator.next_sibling
                else:
                    iterator = iterator.next_sibling.next_sibling

            
            # Add annotations to metadata
            if len(annotations) > 0:
                core_metadata["annotations"] = annotations
            

        if core_metadata == {}:
            core_metadata=None
        ### FOR ADDING A CONTENT NODE, allowing duplicates
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
            core_metadata=core_metadata,
            status=status,
            node_text=node_text,
            addendum=addendum
        )
        insert_node(section_node, TABLE_NAME, debug_mode=True)
        

if __name__ == "__main__":
    main()