
import os
from bs4 import BeautifulSoup


from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List, Tuple
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
from bs4.element import Tag

from pathlib import Path
import sys
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
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup, selenium_element_present, selenium_elements_present
from selenium.webdriver.remote.webelement import WebElement

COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "al"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://alison.legislature.state.al.us"
TOC_URL = "https://alison.legislature.state.al.us/code-of-alabama"
SKIP_TITLE = 21
RESERVED_KEYWORDS = [" RESERVED."]
# === Jurisdiction Specific Global Variables ===
# Selenium Driver
DRIVER = None



def main():
    corpus_node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    global DRIVER
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(5)

    # Find table of content item
    toc_content = DRIVER.find_element(By.ID, "simple-tabpanel-0")
    
    all_titles = toc_content.find_elements(By.CLASS_NAME, "code-item")

    for i, current_element in enumerate(all_titles):
        # Helpful for partial scraping during development
        if i < SKIP_TITLE:
            continue
        recursive_scrape(corpus_node, current_element)
        # To reduce loading times, close unused elements
        current_element.click()

def recursive_scrape(node_parent: Node, current_element: WebElement):
    """
    Scrape all titles on the Table of Contents page.
    """
    
    parent_element = current_element.find_element(By.XPATH, "./..")
    current_element.click()
    # Wait to load
    

    tag_text = current_element.text
    
    level_classifier = tag_text.split(" ")[0].lower()
    number = tag_text.split(" ")[1]
    node_name = tag_text
    core_metadata = None

    # Very Weird Placeholder Level Classifier, found directly under  us/al/statutes/title=21/chapter=1/article=1/section=21-1-1
    ## Deciding to ignore
    if level_classifier == "placeholder":
        return

    # Handle cases where unlabeled SUB levels occur - allow unlabeled 'subsections'
    if level_classifier == node_parent.level_classifier:
        if level_classifier == "section":
            core_metadata = {"mislabeled": "subsection"}
        else:
            level_classifier = "sub"+level_classifier
        


    if level_classifier == "title":
        top_level_title = number
    else:
        top_level_title = node_parent.top_level_title

    node_id = f"{node_parent.node_id}/{level_classifier}={number}"
    node_type = "structure"
    node_text, addendum = None, None
    link = TOC_URL

    # Check if the node is reserved, tag in status
    status=None
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            status="reserved"
            break
   
    if level_classifier == "section":
        # Theres a really weird case where "sections" are used as structure nodes
        # See us/al/statutes/title=12/chapter=21/article=2/division=2 on the official site for an example
        try:
            citation = f"Al. Stat. § {number}"
            # Get the separate section for text
            text_element = WebDriverWait(DRIVER, 20).until(selenium_element_present(parent_element, (By.CLASS_NAME, "html-content")))
            # Don't get node_text and addendum for reserved sections, it's werid stuff
            if not status:
                node_text, addendum = parse_text_element(text_element)
            node_type = "content"
        # Handle Sections which have unlabeled subsections
        except:
            node_type = "structure"
            citation= f"Al. Stat. § Title {top_level_title} {level_classifier} {number}"

       

    else:
        citation= f"Al. Stat. § Title {top_level_title} {level_classifier} {number}"

    node_to_add = Node(
        id=node_id,
        citation=citation,
        link=link,
        status=status,
        node_type=node_type,
        number=number,
        node_name=node_name,
        top_level_title=top_level_title,
        level_classifier=level_classifier,
        parent=node_parent.node_id,
        node_text=node_text,
        addendum=addendum,
        core_metadata=core_metadata
    )
    # No need for further recursion, found content node
    if node_type == "content":
        insert_node(node_to_add, TABLE_NAME, debug_mode=True)
        return
    # parent_element is a Selenium WebElement
    # Find the next recursive element
    try:
        child_elements = WebDriverWait(DRIVER, 20).until(selenium_elements_present(parent_element, (By.CLASS_NAME, "code-item"), 2))
    except:
        # No child elements exist for structure node, must be reserved
        child_elements = []
        node_to_add.status = "reserved"
    
    insert_node(node_to_add, TABLE_NAME, debug_mode=True)

    # Probably need to use WebDriverWait(DRIVER, 20).until())
    
    for i, child_element in enumerate(child_elements):
        # Don't recurse into previously visited node
        if i == 0:
            continue
            
        recursive_scrape(node_to_add, child_element)
        # After recursion, close the element
        child_element.click()


def parse_text_element(text_element: WebElement) -> Tuple[NodeText, Addendum]:
    """
    Given a text element "<div class="html-content> <p>TEXT</p> </div>", return the extracted text in a NodeText pydantic model as well as the section's Addendum.
    """
    # WARNING: NEEDS TESTING TO ENSURE TEXT IS ONLY CONTAINED IN <p> tags!
    #  - COULD BREAK WITH NESTED <p>, or weird tables/pics. CAREFUL!

    node_text = NodeText()
    p_tags = text_element.find_elements(By.TAG_NAME, "p")

    # Alabama Code NodeText is pretty vanilla. All flat <p> tags, no discernible features to extract.
    for i, p_tag in enumerate(p_tags):
        text = p_tag.text
        if text != "":
            node_text.add_paragraph(text=text)

    addendum = Addendum()
    try:
        addendum_tag = text_element.find_element(By.TAG_NAME, "i")
        # Again, bland Addendum. Default to "history" type
        if(addendum_tag.text != ""):
            addendum.history = AddendumType(text=addendum_tag.text)
    except:
        print(f"Could not find addendum_tag!")
    # If no addendum is found/added, set addendum to None
        
    if not addendum.history:
        addendum=None

    return node_text, addendum
    

if __name__ == "__main__":
     main() 