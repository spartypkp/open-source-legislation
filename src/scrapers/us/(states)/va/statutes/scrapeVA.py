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
JURISDICTION = "va"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://law.lis.virginia.gov"
TOC_URL =  "https://law.lis.virginia.gov/vacode/"
RESERVED_KEYWORDS = ["[Repealed]"]


def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    
    scrape_toc(corpus_node)
    

def scrape_toc(node_parent: Node):
    soup = get_url_as_soup(TOC_URL)
    all_titles_container = soup.find(class_="number-descrip-list")
    all_titles = all_titles_container.find_all("a")
    for i, title_container in enumerate(all_titles):
        href = title_container['href']
        link = f"{BASE_URL}{href}"
        title_soup = get_url_as_soup(link)
        title_container = title_soup.find(id="va_code")
        node_name_container = title_container.find("h2")
        node_name = node_name_container.get_text().replace("Read Title ", "").strip()
        
        number = node_name.split(" ")[1]
       
        if number[-1] == ".":
            number = number[:-1]
        
        level_classifier = "title"
        parent = node_parent.node_id
        node_type = "structure"
        node_id = f"{parent}/{level_classifier}={number}"
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
        recursive_scrape(title_container, title_node)




def recursive_scrape(soup: BeautifulSoup, node_parent: Node):
    print(soup.find("dl", recursive=False) is not None)
    if soup.find("dl", recursive=False):
        scrape_chapters(soup, node_parent)
    else:
        
        
        all_containers = soup.find_all("ul", class_="outline", recursive=False)
        
        node_type = "structure"
        parent = node_parent.node_id
        core_metadata = None
        
        for i, container in enumerate(all_containers):
            # Break out of processing chapters hiding as structure nodes
            # Example: https://law.lis.virginia.gov/vacode/title3.2/ 
            if container.find("dl", recursive=False):
                scrape_chapters(soup, node_parent)
                return
            node_name_container = container.find("b")
            node_name = node_name_container.get_text().strip()
            level_classifier = node_name.split(" ")[0].lower()
            number = node_name.split(" ")[1]
            if number[-1] == ".":
                number = number[:-1]
            node_id = f"{node_parent.node_id}/{level_classifier}={number}"

            status = None
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    status = "reserved"
                    break

            structure_node = Node(
                id=node_id,
                link=str(node_parent.link),
                level_classifier=level_classifier,
                node_type=node_type,
                parent=parent,
                status=status,
                node_name=node_name,
                top_level_title=node_parent.top_level_title
            )
            insert_node(structure_node, TABLE_NAME, debug_mode=True) 

            if not status:
                recursive_scrape(container, structure_node)




def scrape_chapters(soup: BeautifulSoup, node_parent: Node):
    all_containers = soup.find("dl").find_all(recursive=False)
    level_classifier = "chapter"
    node_type = "structure"
    parent = node_parent.node_id
    for i, container in enumerate(all_containers):
        # Even index is link: level classifier and number
        if i % 2 == 0:
            status = None
            core_metadata = None
            link_container = container.find("a")
            href = link_container['href']
            link = f"{BASE_URL}{href}"
            link_text = link_container.get_text()
            level_classifier = link_text.split(" ")[0].lower()
            number = link_text.split(" ")[1]
            node_id = f"{parent}/{level_classifier}={number}"
        # Odd index is node_name and descendant information
        else:
            descendants = container.find(class_="secondary-text").get_text()
            core_metadata = {}
            core_metadata["descendants"] = descendants
            node_name = container.get_text().replace(descendants, "")
            for val in RESERVED_KEYWORDS:
                if val in node_name:
                    status = "reserved"
                    break
            # Insert nodes after each odd index
            chapter_node = Node(
                id=node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                status=status,
                top_level_title=node_parent.top_level_title,
                parent=parent,
                core_metadata=core_metadata
            )
            insert_node(chapter_node, TABLE_NAME, debug_mode=True)
            # DO NOT scrape chapters which are repealed/reserved
            if not status:
                scrape_sections(chapter_node)

def scrape_sections(node_parent: Node):

    
    soup = get_url_as_soup(str(node_parent.link))
    level_classifier = "section"
    node_type = "content"   
    parent = node_parent.node_id

    content = soup.find(id="va_code")
    
    all_containers: List[Tag] = content.find_all(["b", "dl"])
    
    for i, container in enumerate(all_containers):
        status=None
        processing = None
       
        

        # Indicates article
        if container.name == "b":
            article_name = container.get_text()
            article_number = article_name.split(" ")[1]
            if article_number[-1] == ".":
                article_number = article_number[:-1]
            article_node_id = f"{node_parent.node_id}/article={article_number}"

            article_status = None
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    article_status = "reserved"
                    break


            article_node = Node(
                id=article_node_id,
                link=node_parent.link,
                top_level_title=node_parent.top_level_title,
                number=article_number,
                node_type="structure",
                node_name=article_name,
                parent=node_parent.node_id,
                level_classifier="article",
                status=article_status
            )
            insert_node(article_node, TABLE_NAME, debug_mode=True)
            parent=article_node.node_id
            continue
        for i, section_a_tag in enumerate(container.find_all("a")):
        
            href = section_a_tag['href']
            link = f"{BASE_URL}{href}"
            
            section_soup = get_url_as_soup(link)
        
            
            section_content = section_soup.find(id="va_code")
            
            node_name_container = section_content.find("h2")
            node_name = node_name_container.get_text().strip()
            
            number = node_name.split(" ")[1]

            if number[-1] == ".":
                number = number[:-1]
            citation = f"Va. Code Ann. § {number}"

            node_id = f"{parent}/section={number}"
            section_text_container = section_content.find("section")
            all_p_tags = section_text_container.find_all(recursive=False)
            
            node_text = NodeText()
            addendum = Addendum()
            

            for i, p_tag in enumerate(all_p_tags):
                # print(i)
                # print(p_tag.prettify())
                references = ReferenceHub()

                text = p_tag.get_text()

                all_a_tags = p_tag.find_all("a")
                for j, a_tag in enumerate(all_a_tags):
                    ref_href = a_tag['href']
                    corpus=None
                    # Indicates from the virginia code
                    if "/vacode" in ref_href:
                        ref_link = f"{BASE_URL}{ref_href}"
                    # Indicates another corpus
                    else:
                        if processing is None:
                            processing = {}
                        ref_link = ref_href
                        if i != len(all_p_tags)-1:
                            processing["unknown_reference_corpus_in_node_text"] = True
                        
                    reference = Reference(text=a_tag.get_text())
                    references.references[ref_link] = reference
                # Remove empty reference hub
                if references.references == {}:
                    references = None
                # print(f"I: {i}, len(all_p_tags): {len(all_p_tags)}")
                # print(i == len(all_p_tags)-1)
                # Ensure last paragraph is always added as the addendum
                if i == len(all_p_tags)-1:
                    addendum.history = AddendumType(text=text, reference_hub=references)
                else:
                    node_text.add_paragraph(text=text, reference_hub=references)
            if processing == {}:
                processing = None
            section_node = Node(
                id=node_id,
                link=link,
                citation=citation,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                status=status,
                top_level_title=node_parent.top_level_title,
                parent=parent,
                node_text=node_text,
                addendum=addendum,
                processing=processing
            )
            insert_node(section_node, TABLE_NAME, debug_mode=True)


if __name__ == "__main__":
     main() 