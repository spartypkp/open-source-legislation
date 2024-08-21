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



COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "in"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"
BASE_URL = "https://iga.in.gov"
TOC_URL = "https://iga.in.gov/laws/2023/ic/titles/main"
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["Repealed", "Expired"]
DRIVER = webdriver.Chrome()

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_toc_url(corpus_node)
        

def scrape_toc_url(node_parent: Node):
    
    DRIVER.get(TOC_URL)
    
    nav_container = DRIVER.find_element(By.ID, "indianaCodeSidenav")
    for i in range(len(nav_container.find_elements(By.XPATH, "./*"))):
        if i < SKIP_TITLE:
            continue
        
        nav_container = DRIVER.find_element(By.ID, "indianaCodeSidenav")
        title_selenium = nav_container.find_elements(By.XPATH, "./*")[i]
        title = BeautifulSoup(title_selenium.get_attribute('outerHTML'), features="html.parser")
    
        
        title = title.find("li", recurisve=False)
        title_button = title.find("button", recursive=False)
        node_name = title_button.get_text().strip()
        
        
        top_level_title = node_name.split(" ")[1]
        number = top_level_title
        if top_level_title[-1] == ".":
            top_level_title = top_level_title[:-1]
        level_classifier = "title"
        node_type = "structure"
        link = f"https://iga.in.gov/laws/2023/ic/titles/{top_level_title}"
        parent=node_parent.node_id
        node_id = f"{parent}/title={top_level_title}"

        title_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=number,
            parent=parent,
        )
        insert_node(title_node, TABLE_NAME, debug_mode=True)
        title_selenium.click()
        
        scrape_article(title_node, i)



def scrape_article(node_parent: Node, title_index: int):
    
    title_selenium = DRIVER.find_element(By.ID, "indianaCodeSidenav").find_elements(By.XPATH, "./*")[title_index]
    article_container = title_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU")
    
    if article_container is None:
        return
    for i in range(len(article_container.find_elements(By.XPATH, "./*"))):
        title_selenium = DRIVER.find_element(By.ID, "indianaCodeSidenav").find_elements(By.XPATH, "./*")[title_index]
        article_container = title_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU")
        article_selenium = article_container.find_elements(By.XPATH, "./*")[i]
        article = BeautifulSoup(article_selenium.get_attribute('outerHTML'), features="html.parser")
        #print(article.prettify())
        article_button = article.find_all(recursive=False)[0]
        node_name = article_button.get_text().strip()
        number = node_name.split(" ")[1]
        if number[-1] == ".":
            number = number[:-1]
        level_classifier = "article"
        node_type = "structure"
        link = f"https://iga.in.gov/laws/2023/ic/titles/{node_parent.top_level_title}#{node_parent.top_level_title}-{number}"
        parent = node_parent.node_id
        node_id = f"{parent}/article={number}"

        status = None
        for keyword in RESERVED_KEYWORDS:
            if keyword in node_name:
                status = "reserved"
                break
        article_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=node_parent.top_level_title,
            parent=parent,
            status=status
        )
        
        insert_node(article_node, TABLE_NAME, debug_mode=True)

        
        if not status:
            article_selenium.click()
            scrape_chapter(article_node, title_index, i)
  


def scrape_chapter(node_parent: Node, title_index: int, article_index: int):
    
    title_selenium = DRIVER.find_element(By.ID, "indianaCodeSidenav").find_elements(By.XPATH, "./*")[title_index]
    article_selenium = title_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU").find_elements(By.XPATH, "./*")[article_index]
    chapter_container = article_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU")
    if chapter_container is None:
        return
    
    for i, chapter_selenium in enumerate(chapter_container.find_elements(By.XPATH, "./*")):
        # Skipping repeated article container
        if i == 0:
            continue
        
        chapter = BeautifulSoup(chapter_selenium.get_attribute('outerHTML'), features="html.parser")

        chapter_button = chapter.find_all(recursive=False)[0]

        node_name = chapter_button.get_text().strip()
        number = node_name.split(" ")[1]
        if number[-1] == ".":
            number = number[:-1]

        article_num = node_parent.number
        
        

        level_classifier = "chapter"
        node_type = "structure"
        status = None
        for keyword in RESERVED_KEYWORDS:
            if keyword in node_name:
                status = "reserved"
                break


        link = f"https://iga.in.gov/laws/2023/ic/titles/{node_parent.top_level_title}#{node_parent.top_level_title}-{article_num}-{number}"
        parent=node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"
        
        chapter_node = Node(
            id=node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=node_parent.top_level_title,
            parent=parent,
            status=status
        )
        
        insert_node(chapter_node, TABLE_NAME, debug_mode=True)
    
        if not status:
            try:
                chapter_selenium.click()
            except:
                DRIVER.execute_script("arguments[0].scrollIntoView();", chapter_selenium)
                chapter_selenium.click()
            scrape_section(chapter_node, title_index, article_index, i)


def scrape_section(node_parent: Node, title_index: int, article_index: int, chapter_index: int):
    global ALL_ELEMENTS
    title_selenium = DRIVER.find_element(By.ID, "indianaCodeSidenav").find_elements(By.XPATH, "./*")[title_index]
    article_selenium = title_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU").find_elements(By.XPATH, "./*")[article_index]
    chapter_selenium = article_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU").find_elements(By.XPATH, "./*")[chapter_index]
    
    
    section_container = chapter_selenium.find_element(By.CLASS_NAME, "ICMenu_menu__3aZYU")
    if section_container is None:
        return
    for i, section_selenium in enumerate(section_container.find_elements(By.XPATH, "./*")):
        # Skipping repeated article container
        if i == 0:
            continue
        section = BeautifulSoup(section_selenium.get_attribute('outerHTML'), features="html.parser")
        section_link = section.find("a")
        node_name = section_link.get_text().strip()
        number = node_name.split(" ")[1]
        if number[-1] == ".":
            number = number[:-1]

        link = BASE_URL + section_link['href']
        citation = link.split("#")[-1]
        level_classifier = "section"
        node_type = "content"
        parent = node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"

        status = None
        for keyword in RESERVED_KEYWORDS:
            if keyword in node_name:
                status = "reserved"
                break
        


        node_text = NodeText()
        addendum = Addendum()
        
        core_metadata = {}
        processing = {}
        status = None
        

        if  "-a" in citation:
            temp_node_citation = citation.split("-a")[0]   
        else:
            temp_node_citation = citation
           

        if ALL_ELEMENTS == []:

            section_selenium.click()
            selenium_root = DRIVER.find_element(By.ID, "main-container").find_element(By.CLASS_NAME, "SideNavLayout_mainContent__1UpKd").find_element(By.CLASS_NAME, "IndianaCode_titleContent__1tjom")
            #print(selenium_root.get_attribute('outerHTML'))
            shadow_root = selenium_root.shadow_root
            
            first_div = shadow_root.find_element(By.ID, f"{temp_node_citation}")
   
            # Execute JavaScript to get all sibling elements of first_div
            
            ALL_ELEMENTS = DRIVER.execute_script('return Array.from(arguments[0].parentNode.children)', first_div)
            # Remove the first_div from the list
         

        # I'm currently refactoring this code, and have no idea what VOODOO magic bullshit I did when I first scraped this. Going to try and refactor without changing anything
        while len(ALL_ELEMENTS) > 0:
            if ALL_ELEMENTS[0].get_attribute('id') is None:
                ALL_ELEMENTS.pop(0)
            elif ALL_ELEMENTS[0].get_attribute('id') == temp_node_citation:
                break
            else:
                ALL_ELEMENTS.pop(0)
        # print(ALL_ELEMENTS[0].text)
        ALL_ELEMENTS.pop(0)
        # print(ALL_ELEMENTS[0].text)
        
        i = 0
        while len(ALL_ELEMENTS) > 0:
            p_raw = ALL_ELEMENTS.pop(0)
            
            p = BeautifulSoup(p_raw.get_attribute('outerHTML'), features="html.parser")
            # print(p)
            # time.sleep(2)
            if str(p)[0:4] == "<div":
                ALL_ELEMENTS.insert(0, p_raw)
                break
            
            
            txt = p.get_text().strip()
            if txt == "":
                continue
            

            if p.find("i") is not None:
                addendum.history = AddendumType(text=p.find("i").get_text().strip())
            
            # Regular text paragraph

            reference_hub = ReferenceHub()
            
                
            for a in p.find_all("a"):
                if 'href' not in a.attrs:
                    continue
                ref_link = BASE_URL+a['href']
                ref_text = a.get_text()

                ref_corpus = None
                # Indicates an <a> tag reference to a different corpus, needs work adding logic. Adding processing tag for now
                if "#" not in a['href']:
                    processing['unknown_reference_corpus_in_node_text'] = True

                reference_hub.references[ref_link] = Reference(text=ref_text, corpus=ref_corpus)
                    
            # Attempting to determine indentation level of paragraph. Remove for now
            # if 'style' in p.attrs:
            #     if p.attrs['style'] != "":
            #         style = p.attrs['style']
            #     else:
            #         style = None
            # else:
            #     style = None
           
            # if style is None:
            #     indentation = 0
            #     text_indentation.append(indentation)
            # elif style == " margin-left: 0.31in":
            #     indentation = 1
            # elif style == " margin-left: 0.4375in":
            #     indentation = 2
            #     text_indentation.append(indentation)
            # else:
            #     indentation = 3
            #     text_indentation.append(indentation)
            
            node_text.add_paragraph(txt, reference_hub=reference_hub)

        if processing == {}:
            processing = None
        if addendum.history is None:
            addendum = None
        
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
            parent=parent,
            status=status
        )
        

        insert_node(section_node, TABLE_NAME, debug_mode=True)
   

def expand_shadow_element(element, driver):
  shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
  return shadow_root

if __name__ == "__main__":
    main()