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
JURISDICTION = "il"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://www.ilga.gov/legislation/ilcs/"
ARTICLE_BASE_URL = "https://www.ilga.gov"
TOC_URL = "https://www.ilga.gov/legislation/ilcs/ilcs.asp"
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["(Repealed"]


def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_toc_page(corpus_node)

def scrape_toc_page(node_parent: Node):
    soup = get_url_as_soup(TOC_URL)
    # Very complicated, sorry for this. Incredibly helpful for debugging purposes
    statutes_container = soup.find(id="toplinks")
    statutes_container = statutes_container.find("center")
    statutes_container = statutes_container.find("table")
    
    
    statutes_container = statutes_container.find("tr")
    statutes_container = statutes_container.find_all("td")[1]
    # I think this is a BS parse error <p> should not be nesting everything
    all_p_tags = statutes_container.find_all("p")
    for i, bad_p_tag in enumerate(all_p_tags):
        bad_p_tag.unwrap()

    statutes_container = statutes_container.find("ul")
   

    all_chapter_containers: List[Tag] = statutes_container.find_all(recursive=False)
    
    current_category=""
    nonBreakSpace = u'\xa0'

    for i, chapter_container in enumerate(all_chapter_containers):
        # P tags are empty, used for formatting
        
        # Divs indicate categories for following nodes, mark for later
        if chapter_container.name == "div":
            current_category = chapter_container.get_text().strip()
            continue
        
        link_container = chapter_container.find("a")
        href = link_container['href']
        link = f"{BASE_URL}{href}"
        level_classifier="chapter"
        node_type = "structure"
        parent = node_parent.node_id
        core_metadata = {"category": current_category}
        node_name = link_container.get_text().strip()
       
        node_name = node_name.replace(nonBreakSpace, ' ')
        # Stupid &nbsp
        node_name_temp = node_name.replace("CHAPTER", "").strip()

        number = node_name_temp.split(" ")[0]
        node_id = f"{parent}/chapter={number}"

        chapter_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=number,
            parent=parent,
            core_metadata=core_metadata
        )
        insert_node(chapter_node, TABLE_NAME, debug_mode=True)
        scrape_acts(chapter_node)

    

def scrape_acts(node_parent: Node):
    soup = get_url_as_soup(str(node_parent.link))

    top_links = soup.find(id="toplinks").parent
    top_links = top_links.find("table")
    top_links = top_links.find("tr")
    top_links = top_links.find_all("td")[1]
    # I think this is a BS parse error <p> should not be nesting everything
    all_p_tags = top_links.find_all("p")
    for i, bad_p_tag in enumerate(all_p_tags):
        bad_p_tag.unwrap()

    all_br_tags = top_links.find_all("br")
    for i, bad_br_tag in enumerate(all_br_tags):
        bad_br_tag.decompose()

    top_links = top_links.find("ul")
    
    
    # Again, sorry for the nesting. Blame Illinois.
    all_act_containers: List[Tag] = top_links.find_all(recursive=False)
    
    nonBreakSpace = u'\xa0'
    current_category = ""
    for i, act_container in enumerate(all_act_containers):
        
        # Bold indicates category heading
        category_heading = act_container.find("b")
       

        if category_heading is not None:
            current_category = act_container.get_text().strip()
            continue

        link_container = act_container.find("a")
        href = link_container['href']
        link = f"{BASE_URL}{href}"
        level_classifier="act"
        node_type = "structure"
        parent = node_parent.node_id
        # Only add categories when actually present
        core_metadata = {}
        if current_category != "":
            core_metadata["category"] = current_category

        node_name = link_container.get_text().strip()
        node_name = node_name.replace(nonBreakSpace, ' ')
        
        number = node_name.split("/")[0]
        number = number.split(" ")[2]
        node_id = f"{parent}/act={number}"

        status = None
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                status = "reserved"
                break

        if core_metadata == {}:
            core_metadata = None

        act_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=node_parent.top_level_title,
            parent=parent,
            core_metadata=core_metadata,
            status=status
        )
        insert_node(act_node, TABLE_NAME, debug_mode=True)

        # Simply continue when repealed acts occurr
        if status:
            continue

        article_soup = get_url_as_soup(link)
        all_article_containers: List[Tag] = article_soup.find_all(class_="indent-10")

        # Scrape articles BEFORE scraping sections. Needs testing
        if len(all_article_containers) == 0:
            scrape_sections(act_node, article_soup)
        else:
            
            for article_container in all_article_containers:
                node_type = "structure"
                level_classifier = "article"
                

                node_name = article_container.get_text()
                number = node_name.split(" ")[1]
                article_parent = act_node.node_id
                article_node_id = f"{article_parent}/{level_classifier}={number}"
                article_node = Node(
                    id=article_node_id,
                    link=link,
                    node_type=node_type,
                    level_classifier=level_classifier,
                    number=number,
                    node_name=node_name,
                    top_level_title=node_parent.top_level_title,
                    parent=article_parent
                )
                insert_node(article_node, TABLE_NAME, debug_mode=True)
            exit(1)
            scrape_sections(act_node)

   

# I don't know why this is needed. Will investigate this mega legacy code (ex-cofounder wrote this shi, not me)
# def scrape_article(url, article_name, top_level_title, node_parent):
#     response = urllib.request.urlopen(url)
#     data = response.read()      # a `bytes` object
#     text = data.decode('utf-8', errors='ignore') # a `str`;
#     soup = BeautifulSoup(text, features="html.parser")

#     node_type = "structure"
#     node_level_classifier = "ARTICLE"
#     node_name = article_name
#     node_number = article_name.split(" ")[1]
#     node_link = url
#     node_id = f"{node_parent}{node_level_classifier}={node_number}/"
#     node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
#     insert_node_ignore_duplicate(node_data)
#     section_node_parent = node_id

#     section_header = soup.find("div", class_="heading")
#     section_container = section_header.find_next_sibling("p")
#     scrape_sections(node_link, section_container, top_level_title, section_node_parent)



def scrape_sections(node_parent: Node, soup: BeautifulSoup):
    nonBreakSpace = u'\xa0'
    
    section_titles: List[Tag] = soup.find_all("title")
    section_parent = node_parent.node_id
    link = str(node_parent.link)
   

    for i, title_tag in enumerate(section_titles):
        # Skip chapter heading
        if i == 0:
            continue

        citation = title_tag.get_text().strip()
        number = citation.split("/")[-1].rstrip(".")
        node_text_container = title_tag.find_next("table")
        link_container = title_tag.find_next("a")
        link = f"https://www.ilga.gov{link_container['href']}"
        node_name = ""
        

        if "Art. " in number:
            # Article Stuff
            node_type = "structure"
            level_classifier = "article"

            article_addendum = Addendum(source=AddendumType(type="source", text=""))

            article_paragraph_containers = node_text_container.find_all("code")
            valid_article_containers = 0
            for i, paragraph_container in enumerate(article_paragraph_containers):
                text = paragraph_container.get_text().strip().replace(nonBreakSpace, "")
                # Skip empty <code> blocks
                if text == "":
                    continue
                # 0 - citation
                if valid_article_containers == 0:
                    valid_article_containers += 1
                    continue
               
                # 1 & 2 - node_name
                if valid_article_containers == 1:
                    node_name = text
                    valid_article_containers += 1
                    continue

                #  # 3 - addendum source
                # if valid_article_containers == 1:
                #     article_addendum.source.text = text
                #     valid_article_containers += 1
                #     continue
                
            
            number = node_name.split(" ")[1]
            if number[-1] == ".":
                number = number[:-1]

            status = None
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    status = "reserved"
                    break

            article_parent = node_parent.node_id
            article_node_id = f"{article_parent}/{level_classifier}={number}"
            article_node = Node(
                id=article_node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=node_parent.top_level_title,
                parent=article_parent,
                citation=citation,
                addendum=article_addendum,
                status=status
            )
            insert_node(article_node, TABLE_NAME, debug_mode=True)
            section_parent = article_node_id
        ## 
        else:

        
            node_type = "content"
            level_classifier = "section"
            node_id = f"{section_parent}/{level_classifier}={number}"
            
            
            
            # Needs testing
            node_name = ""

            node_text = NodeText()
            addendum = Addendum(source=AddendumType(type="source", text=""), history=AddendumType(type="history", text=""))
            
            section_paragraph_containers = node_text_container.find_all("code")
            
           
            valid_containers = 0
            for i, paragraph_container in enumerate(section_paragraph_containers):
                text = paragraph_container.get_text().replace(nonBreakSpace, "")
                
                # Skip empty <code> blocks
                if text.strip() == "":
                    # Dirty check to see if we can add a node name end
                    continue
                #print(f"Text: {text}, valid_containers:{valid_containers}")
                # 0 - citation
                if valid_containers == 0:
                    valid_containers += 1
                    continue
               
                if "(from " in text:
                    addendum.history.text = text.strip()
                    continue
                if text.strip() == ".)":
                    continue
                # 1 - node_name start
                if valid_containers == 1:
                    node_name = text.strip()
                    valid_containers += 1
                    continue
                # 2 - OPTIONAL continuation of the node_name
                # if valid_containers == 2 and ((i == node_name_index+2) or (i == node_name_index+1)):
                #     # This is all fucked
                #     if valid_node_name_end(text):
                #         node_name_end = " " + text.strip()
                #         check_node_name_index = i
                #         valid_containers += 1
                #     continue
                text = text.strip()
                
                # Rest of paragraphs
                if "(Source:" in text:
                    addendum.source.text += text + ".)"
                else:
                    node_text.add_paragraph(text=text)
            
            if addendum.history.text == "":
                addendum.history = None
            if addendum.source.text == "":
                addendum.source = None
                
            status = None
            node_name = node_name.strip()
            section_node = Node(
                id=node_id,
                link=link,
                citation=citation,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                node_text=node_text,
                addendum=addendum,
                top_level_title=node_parent.top_level_title,
                parent=section_parent,
                status=status
            )
            
            
            insert_node(section_node, TABLE_NAME, debug_mode=True)


def valid_node_name_end(text: str):
    alphabet = "abcdefghijklmnopqrstuvwxyz."
    for i in range(len(text)-2, -1, -1):
        if text[i] in alphabet:
            if text[i] + text[i+1] == ". ":
                return True
            break
    return False

if __name__ == "__main__":
    main()