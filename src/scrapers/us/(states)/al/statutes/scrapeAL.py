
import os
from bs4 import BeautifulSoup


from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List, Tuple

import time
from bs4.element import Tag

DIR = os.path.dirname(os.path.realpath(__file__))

from src.utils.pydanticModels import NodeID, Node, Addendum, AddendumType, NodeText, Paragraph, ReferenceHub, Reference, DefinitionHub, Definition, IncorporatedTerms
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup
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
SKIP_TITLE = 9
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

    toc_content = DRIVER.find_element(By.ID, "simple-tabpanel-0")
    all_titles = toc_content.find_elements(By.CLASS_NAME, "code-item")

    for i, current_element in enumerate(all_titles):
        # Helpful for partial scraping during development
        if i < SKIP_TITLE:
            continue
        recursive_scrape(corpus_node, current_element)

def recursive_scrape(node_parent: Node, current_element: WebElement):
    """
    Scrape all titles on the Table of Contents page.
    """
    parent_element = current_element.find_element(By.XPATH, "./..")
    current_element.click()
    time.sleep(0.25)

    tag_text = current_element.text
    level_classifier = tag_text.split(" ")[0].lower()
    number = tag_text.split(" ")[1]
    node_name = tag_text


    if level_classifier == "title":
        top_level_title = number
    else:
        top_level_title = node_parent.top_level_title
    node_id = f"{node_parent.node_id}/{level_classifier}={number}"
    node_type = "structure"
    node_text, addendum = None, None
    link = TOC_URL

    status=None
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            status="reserved"
            break
    
    if level_classifier == "section":
        citation = f"Al. Stat. § {number}"
        # Get the separate section for text
        text_element = parent_element.find_element(By.CLASS_NAME, "html-content")
        # Don't get node_text and addendum for reserved sections, it's werid stuff
        if not status:
            node_text, addendum = parse_text_element(text_element)
        node_type = "content"

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
        addendum=addendum
    )
    print(f"-Inserting {node_id}")
    insert_node(node_to_add, TABLE_NAME)

    

    
    next_elements = parent_element.find_elements(By.CLASS_NAME, "code-item")
    # citation= f"Al. Stat. § {number}"
    for i, next_element in enumerate(next_elements):
        if i == 0:
            continue
                
        recursive_scrape(node_to_add, next_element)

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