


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



COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "ca"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = 'https://leginfo.legislature.ca.gov/'
TOC_URL = "https://leginfo.legislature.ca.gov/faces/codes.xhtml"
SKIP_TITLE = 0 

all_codes: List[Tuple[str, str]] = [("BPC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=BPC" ),("CIV","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CIV" ),("CCP","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CCP" ),("COM","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=COM" ),("CORP","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CORP" ),("EDC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=EDC" ),("ELEC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=ELEC" ),("EVID","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=EVID" ),("FAM","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FAM" ),("FIN","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FIN" ),("FGC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FGC" ),("FAC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FAC" ),("GOV","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=GOV" ),("HNC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=HNC" ),("HSC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=HSC" ),("INS","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=INS" ),("LAB","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=LAB" ),("MVC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=MVC" ),("PEN","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PEN" ),("PROB","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PROB" ),("PCC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PCC" ),("PRC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PRC" ),("PUC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PUC" ),("RTC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=RTC" ),("SHC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=SHC" ),("UIC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=UIC" ),("VEH","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=VEH" ),("WAT","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=WAT" ),("WIC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=WIC" )]
ALLOWED_LEVELS = ["code", "division", "part", "title", "chapter", "article", "section"]
RESERVED_KEYWORDS = ["(reserved)", "[reserved]"]

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape(corpus_node)


# Current 
# class=treecodetitle
def scrape(corpus_node: Node):

    # This is beyond messy. California likes to move the ordering of their levels around based on the different code. This is a way to track those. This took 30+ hours of research. And it's messy, I'm sorry.

    DIVISION_CASE = ["DIVISION", "PART", "TITLE", "CHAPTER", "ARTICLE"]
    PART_CASE = ["PART", "TITLE", "DIVISION", "CHAPTER", "ARTICLE"]
    TITLE_CASE = ["TITLE", "DIVISION", "PART", "CHAPTER", "ARTICLE"]
    SHORT_CASE = ["DIVISION", "CHAPTER", "ARTICLE"]
    REGULAR_CASE = ["DIVISION", "PART", "CHAPTER", "ARTICLE"]
    BASE = ["ca", "statutes", "code"]

    DIVISION_CODE = ["WAT", "CIV"]
    PART_CODE = ["CCP", 'PEN']
    TITLE_CODE = ["GOV", "CORP", "EDC"]
    SHORT_CODE = ["VEH", "COM", "FIN", "EVID"]
    
    for i, code_tup in enumerate(all_codes):
       
        code: str = code_tup[0]
        url = code_tup[1]
        print(f"Scraping for code: {code}")
        title_schema = []

        if (code in DIVISION_CODE):
            title_schema = DIVISION_CASE
        elif (code in PART_CODE):
            title_schema = PART_CASE
        elif (code in TITLE_CODE):
            title_schema = TITLE_CASE
        elif (code in SHORT_CODE):
            title_schema = SHORT_CASE
        else:
            title_schema = REGULAR_CASE
        title_schema = BASE + title_schema

        code_node = Node(
            id=f"{corpus_node.node_id}/code={code.lower()}", 
            link=url, 
            citation=f"Cal. {code.lower()}",
            parent=corpus_node.node_id, 
            number=code.lower(),
            top_level_title=code.lower(), 
            node_type="structure", 
            level_classifier="code"
        )
        insert_node(code_node, TABLE_NAME, ignore_duplicate=True, debug_mode=True)
        scrape_structure_nodes(url, title_schema, code_node, code)
        
# For every root node, scrape all structure nodes, getting a list of all valid HTML div elements which have content node children
def scrape_structure_nodes(url: str, title_schema: List[str], node_parent: Node, top_level_title: str):
    soup = get_url_as_soup(url=url)
    
    # Find the HTML container for actual content
    codesbrchfrm = soup.find(id="codesbrchfrm")
    if (not codesbrchfrm):
        print("Couldn't find codesbrchform!")
        exit(1)
    
    branchChildren = codesbrchfrm.find_all(recursive=False)
    
    container = branchChildren[4].contents[0]
    
    if (not container):
        print("code container undefined!")
        exit(1)

    div_elements = []
    # vFind all div_elements in container
    for i, current_element in enumerate(container.find_all(recursive=False)):
        
        # Format Div
        if (i % 2 == 1):
            continue
        
        div_elements.append(current_element)
        
    
    scrape_per_code(div_elements, title_schema, node_parent)
    return node_parent


def scrape_per_code(structure_divs, title_schema: List[str], node_parent: Node):
    current_node = node_parent
    # Find the container
    
    for i, div in enumerate(structure_divs):
        # Skip useless style divs
        new_partial_node: Node = get_structure_node_attributes(div, current_node)

        # Check node is not reserved
        if new_partial_node.status:
            new_partial_node.node_id += f"/{new_partial_node.level_classifier}={new_partial_node.number}"
            new_partial_node.parent = current_node.node_id

            insert_node(new_partial_node, TABLE_NAME, debug_mode=True)
            return

        # Check if node level classifier is in title schema
        if (new_partial_node.level_classifier not in title_schema):
            
            index = title_schema.index(current_node.id.current_level[0]) + 1
            # Couldn't find the new level_classifier in the title_schema
            if(index == len(title_schema)):
                # Indicates a section by the link attribute _displayText
                if ("codes_displayText" in new_partial_node.node_link):
                    new_partial_node.level_classifier = "section"
                else:
                    # Allow for 'subtitle', 'subchapter', 'subpart' etc...
                    new_partial_node.level_classifier = "sub" + current_node.level_classifier
            else:
                new_partial_node.level_classifier = title_schema[index]
            
        if (new_partial_node.level_classifier in title_schema):
            # Actually build node
            # POSSIBLY ADD

            currentRank = title_schema.index(current_node.level_classifier)
            newRank = title_schema.index(new_partial_node.level_classifier)

            # Determine the position of the newNode in the hierarchy
            if (newRank <= currentRank):
                temp_node_id = current_node.id

                while (title_schema.index(temp_node_id.current_level[0]) > newRank):
                    temp_node_id = temp_node_id.pop_level()
                    if (temp_node_id.current_level[0] == 'code'):
                        break
                    
                
                current_node = temp_node_id
                currentRank = title_schema.index(current_node.current_level[0])
                # Set the ID of the newNode and add it to the current_node's children or siblings
                if (newRank == currentRank):
                

                    new_partial_node.id = f"{current_node.pop_level().raw_id}/{new_partial_node.level_classifier}={new_partial_node.number}"
                    
                    
                    new_partial_node.parent = current_node.pop_level().raw_id
                    
                    current_node = new_partial_node
                else:
                    new_partial_node.id = f"{temp_node_id}/{new_partial_node.level_classifier}={new_partial_node.number}"
                    
                    
                    new_partial_node.parent = current_node.raw_id
                    current_node = new_partial_node
                
            else:
                # Set the ID of the newNode and add it to the current_node's children
                new_partial_node.id.add_level(new_partial_node.level_classifier, new_partial_node.number)
                new_partial_node.parent = current_node.node_id
                current_node = new_partial_node
            

            # Print the current_node and scrape content if necessary
            current_node.node_id = current_node.node_id.replace("./", "/")
            print(current_node)
            insert_node(current_node, TABLE_NAME, debug_mode=True)
            
            #print(current_node)
            if ("codes_displayText" in  new_partial_node.link):
                scrape_content_node(new_partial_node)
        elif ("codes_displayText" in  new_partial_node.link):
                
                #print(f"Scraping all content for {new_partial_node.node_id}")
                new_partial_node.node_id += new_partial_node.level_classifier + "=" + new_partial_node.number
                new_partial_node.parent = current_node.node_id
    
                insert_node(new_partial_node, TABLE_NAME, debug_mode=True)
                scrape_content_node(new_partial_node)
        
            
    


    

def get_structure_node_attributes(current_element, node_parent: Node) -> Node:
    """
    For a structure node, initially populate the attributes into a Pydantic model. The true correct node_id and parent are uncertain, as the correct hierarchy has to be determined later.

    """
    # Find the "a" tag inside the current_element
    #print(current_element.name)
    a_tag = current_element.find("a")

    # Ensure the a_tag is found
    if (not a_tag):
        print("No 'a' tag found in the current element.")
        exit(1)
    # Extract href value
    link = BASE_URL + a_tag["href"]
    if (link is None):
        print("Invalid link!")
        exit(1)
    
    # Assume the first child element of a_tag contains the title and name
    node_name: str = a_tag.contents[0].get_text().strip()
    if (not node_name):
        print("No first child element with text found in the 'a' tag.")
        exit(1)

    print(node_name)
    
    # Check that the current node is not reserved, tag in status if it is
    status=None
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            status="reserved"
            break
    
    # Handle cases where no level is specified, assume appendix
    level_classifier = node_name.split(" ")[0].lower()
    if level_classifier not in ALLOWED_LEVELS:
        level_classifier = "appendix"
        # Example: node_name = "GENERAL PROVISIONS"
        # number should be "GENERAL PROVISIONS", same as node_name
        number=node_name
    else:
        number = node_name.split(" ")[1]

    # Remove unneccesary punctuation
    if(number[-1] == "."):
        number = number[:-1]

    node_type = "structure"
    
        
    # Create a temporary node_id. This will be changed when the correct parent is found
    node_id = f"{node_parent.node_id}"
    citation = f"Cal. {node_parent.top_level_title} {level_classifier} {number}"
    
    partial_node_data = Node(
        id=node_id, 
        link=link,
        citation=citation,
        number=number,
        parent=node_parent.node_id, 
        top_level_title=node_parent.top_level_title, 
        node_type=node_type, 
        level_classifier=level_classifier, 
        status=status,
        node_name=node_name
    )
    print(partial_node_data)
    return partial_node_data
    
    

def scrape_content_node(node_parent: Node):
    """
    Scrape all individual sections.
    """

    soup = get_url_as_soup(url=node_parent.link)

    container = soup.find(id="manylawsections")
    if (not container):
        print("manylawsections container not found!")
        return

    divCon = container.contents[-1]
    if (not divCon):
        print("divCon element cannot be found!")
        exit(1)


    fontContainer = divCon.contents[0]
    if (not fontContainer):
        print("font element cannot be found!")
        exit(1)

    section_divs = fontContainer.find_all("div", recursive=False)
    
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=BPC&sectionNum=Section 115.
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=BPC&sectionNum=115.
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=1358.1.
    
    for i, div in enumerate(section_divs):
        if i == 0:
            continue
        #print(div)
        # find first child div element and extract the .textContent
        try:
            section_container = div.find("a")
            number = section_container.get_text().strip()
            citation = f"Cal. {node_parent.top_level_title} § {number}"
            level_classifier = "section"
            node_id = f"{node_parent.node_id}/{level_classifier}={number}"
            link = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode={node_parent.top_level_title}&sectionNum={number}"
            node_name = "Section " + number
            node_type = "content"
            node_text = NodeText()
        except:
            continue
        
        
        print(f"{node_name},",end="")
        
        for i, p_tag in enumerate(div.find_all(recursive=True)):
            if i <= 1 or p_tag.name == "i":
                continue
            
            text_to_add = p_tag.get_text().strip()
            if(text_to_add == ""):
                continue
            #if len(node_text)==0:
                #text_to_add = node_name + " " + text_to_add
            
            node_text.add_paragraph(text=text_to_add)

        node_addendum_text = node_text.pop()
        addendum = Addendum(history=AddendumType(text=node_addendum_text))
        section_node = Node(
            id=node_id, 
            link=link,
            citation=citation,
            top_level_title=node_parent.top_level_title,
            node_type=node_type,
            level_classifier=level_classifier,
            node_name=node_name,
            number=number,
            node_text=node_text,
            addendum=addendum,
            parent=node_parent.node_id
        )

        insert_node(section_node, TABLE_NAME, False, True)
                
    return

if __name__ == "__main__":
    main()