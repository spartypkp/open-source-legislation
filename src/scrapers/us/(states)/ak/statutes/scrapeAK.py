
import os
from bs4 import BeautifulSoup


from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains

from typing import List, Tuple
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
from bs4.element import Tag
import sys
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
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, selenium_element_present, selenium_elements_present



COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "ak"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"


# The base URL of the corpus's official .gov website
BASE_URL = "https://www.akleg.gov"
# The URL of the Table of Contents
TOC_URL = "https://www.akleg.gov/basis/statutes.asp"
# Start scraping at a specific top_level_title
SKIP_TITLE = 0 # 0/47 titles
RESERVED_KEYWORDS = ["Repealed"]

# === Jurisdiction Specific Global Variables ===
# Selenium Driver
DRIVER = None



def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(country_code=COUNTRY, jurisdiction_code=JURISDICTION, corpus_code=CORPUS)
    scrape_all_titles(corpus_node)

def scrape_all_titles(corpus_node: Node):
    global DRIVER
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)

    
    
    toc_nav_container = DRIVER.find_element(By.ID, "TOC_A")
    toc_nav_container.click()
    
    
    for i in range(SKIP_TITLE, 47):
        titles_container = WebDriverWait(DRIVER, 20).until(selenium_element_present(DRIVER, (By.ID, "TitleToc")))
        all_titles = WebDriverWait(DRIVER, 20).until(selenium_elements_present(titles_container, (By.TAG_NAME, "li")))

        title_container = all_titles[i]

        title_a_tag = title_container.find_element(By.TAG_NAME, "a")

        title_name = title_a_tag.text.strip()
        top_level_title = title_name.split(" ")[1]
        if top_level_title[-1] == ".":
            top_level_title = top_level_title[:-1]
        
        # I want to convert top level title to a string with leading zeros ex: 1 -> 01, 21 -> 21
        
        
        citation = top_level_title.zfill(2)
        link = TOC_URL + "#" + citation
        node_type = "structure"
        level_classifier = "title"
        title_node_id = f"{corpus_node.node_id}/{level_classifier}={top_level_title}"
        

        ### Get title information, Add title node
        title_node = Node(
            id=title_node_id,
            top_level_title=top_level_title,
            number=top_level_title,
            node_type=node_type,
            node_name=title_name,
            level_classifier=level_classifier,
            citation="AS " + citation,
            link=link,
            parent=corpus_node.node_id
        )
        
        insert_node(node=title_node, table_name=TABLE_NAME, ignore_duplicate=True, debug_mode=True)

        print(title_a_tag.text)  
        time.sleep(20)
        title_a_tag.click()
        

        scrape_all_chapters(title_node)
        title_return = DRIVER.find_element(By.ID, "titleLink")
        title_return.click()
        

def scrape_all_chapters(node_parent: Node):
    global DRIVER
    
    chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
    
    _all_chapters = len(chapters_container.find_elements(By.TAG_NAME, "a"))

    for i in range(0, _all_chapters):
        #print(i)
        chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
        all_chapters = chapters_container.find_elements(By.TAG_NAME, "li")
        chapter_container = all_chapters[i]
        chapter_a_tag = chapter_container.find_element(By.TAG_NAME, "a")
        chapter_a_soup = BeautifulSoup(chapter_a_tag.get_attribute("outerHTML"), features="html.parser")
        #print(chapter_a_soup.prettify())

        chapter_name = chapter_a_soup.get_text()
        #print(f"Chapter: {chapter_name}")
        if "No Sections" in chapter_name:
            return
        chapter_number = chapter_name.split(" ")[1]
        if chapter_number[-1] == ".":
            chapter_number = chapter_number[:-1]
        
        node_type = "structure"
        level_classifier = "chapter"
        
        citation =  node_parent.citation + "." + chapter_number
        chapter_number = str(int(chapter_number))
        link = TOC_URL + "#" + citation

        status=None
        for word in RESERVED_KEYWORDS:
            if word in chapter_name:      
                status = "reserved"
                break

        node_id = f"{node_parent.node_id}/{level_classifier}={chapter_number}"
        chapter_node = Node(
            id=node_id,
            top_level_title=node_parent.top_level_title,
            node_type=node_type,
            number=chapter_number,
            node_name=chapter_name,
            level_classifier=level_classifier,
            citation=citation,
            link=link,
            parent=node_parent.parent,
            status=status
        )
        
        insert_node(node=chapter_node, table_name=TABLE_NAME, debug_mode=True)
            
        
        # If chapter is not reserved
        if not status:
            chapter_a_tag.click()
            
            scrape_all_sections(chapter_node)
            chapter_return = DRIVER.find_element(By.ID, "partHead").find_element(By.TAG_NAME, "a")
            chapter_return.click()

        
        
def scrape_all_sections( node_parent: Node):
    
    sections_container = DRIVER.find_element(By.ID, "ChapterToc")
    
    _all_sections = sections_container.find_elements(By.TAG_NAME, "li")

    # can I call this concurrently with
    for i in range(0, len(_all_sections)):
        #print(f"Index: {i}")
        sections_container = DRIVER.find_element(By.ID, "ChapterToc")
        
        all_sections = sections_container.find_elements(By.TAG_NAME, "li")

        section_container_raw = all_sections[i].find_element(By.TAG_NAME, "a")
        section_container = BeautifulSoup(section_container_raw.get_attribute("outerHTML"), features="html.parser")

        node_name = section_container.get_text().strip()
        
        
        if "No Sections" in node_name:
            return
        
        number = node_name.split(" ")[1]
        found_article = False
        
        if number[-1] == ".":
            number = number[:-1]
        
        citation = number

        number = number.split(".")[-1]
        # Remove any leading zeros ex: 005 -> 5
        number = str(int(number))
        

        
        node_type = "content"
        level_classifier = "section"
        link = TOC_URL + "#" + citation
        node_text=None

        status=None
        for word in RESERVED_KEYWORDS:
            if word in node_name:
                status = "reserved"
                break
        

        # TODO: Needs refactoring to work with Pydantic Models
        if not status:
            
            #Example section link:  https://www.akleg.gov/basis/statutes.asp#02.15.010
            
            section_driver = webdriver.Chrome()
            section_driver.get(link)
            
            content = section_driver.find_element(By.ID, "content")

            addendum_container_raw = WebDriverWait(DRIVER, 20).until(selenium_element_present(content, (By.ID, "sideSection")))      
            addendum_container = addendum_container_raw.find_element(By.TAG_NAME, "div")
                    
            section_soup = BeautifulSoup(section_driver.page_source, features="html.parser").body
            
            all_text_container = section_soup.find(id="content")
            
            text_container = all_text_container.find("a", attrs={"name": citation})
            iterator = text_container.parent

            # Find parent article
            for tag in iterator.previous_elements:
                if not isinstance(tag, Tag):
                    continue
                
                if tag.find("h7") is not None:
                    article_container = tag.find("h7")
                    article_name = article_container.get_text().strip()
                    article_number = article_name.split(" ")[1]

                    if article_number[-1] == ".":
                        article_number = article_number[:-1]
                    article_node_type = "structure"
                    article_node_level_classifier = "article"
                    

                    article_node_id = f"{node_parent.node_id}/{article_node_level_classifier}={article_number}"
                    article_node = Node(
                        id=article_node_id,
                        top_level_title=node_parent.top_level_title,
                        number=article_number,
                        node_type=article_node_type,
                        node_name=article_name,
                        level_classifier="article",
                        citation=f"{node_parent.citation} Article {article_number}",
                        link=link,
                        parent=node_parent.parent,
                        status=status
                    )

                    insert_node(article_node, table_name=TABLE_NAME, debug_mode=True)
                    
                    found_article = True
                    break

            
            node_text = NodeText()
            
            # This is so dirty, and I apologize for this shit
            while True:
                reference_hub = None
                iterator = iterator.next_sibling
                if iterator is None:
                    break
                # If the element is a BS4 Tag
                if isinstance(tag, Tag):
                    # Skip bold
                    if iterator.name == "b":
                        break
                    
                    # Get the text, remove whitespace, check if tag is anchor tag
                    txt = iterator.get_text().strip()
                    if iterator.name == "a":
                        if reference_hub is None:
                            reference_hub = ReferenceHub()
                        href = iterator["href"]
                        # Indicates a same-site (same corpus) reference, corpus is None
                        if "#" in href:
                            ref_link = "https://www.akleg.gov/basis/" + href
                            reference = Reference(text=txt, placeholder=None)
                            reference_hub.references[ref_link] = reference
                        # Indicates an external site (different corpus) reference, set corpus to other
                        # TODO: Experiment for common outgoing corpus tags and incorporate logic here
                        else:
                            reference = Reference(text=txt, placeholder=None, corpus="other")
                            reference_hub.references[href] = reference
                            
                    if txt == "":
                        continue
                    node_text.add_paragraph(text=txt, reference_hub=reference_hub)
                else:
                    txt = iterator
                    #print(txt)
                    if txt == "":
                        continue
            # Process the addendum container
            addendum_container = BeautifulSoup(addendum_container.get_attribute("outerHTML"), features="html.parser").find("div")
            addendum = Addendum()
            core_metadata = {}
            if addendum_container is not None:
                
                category = None
                for i, element in enumerate(addendum_container.contents):
                    
                    if isinstance(element, Tag):
                        if element.name == "br":
                            continue
                        txt = element.get_text().strip()
                        #print(txt)
                        if element.name == "h5":
                            category = element.get_text().strip()
                            continue
                        
                        if element.name == "a":
                            href = element["href"]
                            tag_link = "https://www.akleg.gov/basis/" + href
                            
                            if category not in core_metadata:
                                core_metadata[category] = []
                        
                            core_metadata[category].append({"citation": txt, "link": tag_link})
                            
                    else:
                        txt = element
                        
                        if txt == "":
                            continue
                        if "History." in txt:
                            addendum.history = AddendumType(text=txt)
                            break
                        if "REFERENCES" in category:
                            continue

                        core_metadata[category][-1]['text'] = txt   

        if found_article:
            section_node_id = f"{article_node_id}/{level_classifier}={number}"
            parent=article_node_id

        else:
            section_node_id = f"{node_parent.node_id}/{level_classifier}={number}"
            parent=node_parent.node_id

        # Don't pollute rows with empty dictionaries
        if core_metadata == {}:
            core_metadata=None
        
        section_node = Node(
            id=section_node_id, 
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            number=number, 
            node_name=node_name, 
            level_classifier=level_classifier, 
            node_text=node_text, 
            citation="AS " + citation, 
            link=link, 
            addendum=addendum, 
            parent=parent, 
            core_metadata=core_metadata
        )
        
        insert_node(section_node, TABLE_NAME, debug_mode=True)
        

if __name__ == "__main__":
    main()