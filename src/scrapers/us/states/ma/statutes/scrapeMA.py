import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import json
from bs4.element import Tag



RESERVED_KEYWORDS = ["Repealed,"]


 = "madeline"
TABLE_NAME = "ma_node"
BASE_URL = "https://malegislature.gov"
TOC_URL = "https://malegislature.gov/Laws/GeneralLaws"
SKIP_TITLE = 0 
# List of words that indicate a node is reserved



def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_levels(url)
    

def scrape_levels(url):
    
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(.25)
    og_parent = "ma/statutes/"
    
    part_container = DRIVER.find_element(By.CLASS_NAME, "content")
        
    part_soup = BeautifulSoup(part_container.get_attribute("innerHTML"), features="html.parser")
    
    part_name = part_soup.find("h2", id="skipTo") 
  
    node_name = get_text_clean(part_name)
    node_level_classifier = "PART"
    node_type = "structure"
    node_link = url
    node_number = node_name.split(" ")[1].rstrip(":")
    node_id = f"{og_parent}{node_level_classifier}={node_number}/"
    top_level_title = node_number
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)

    title_node_parent = node_id
    
    insert_node(node_data)
    print(node_id)
   

    
    titles_container = DRIVER.find_element(By.ID, "accordion")
    num_titles = len(titles_container.find_elements(By.XPATH, "./div"))
    print(titles_container)
    print(num_titles)
    
    for i in range(0, num_titles):
        titles_container = DRIVER.find_element(By.ID, "accordion")
        title = titles_container.find_elements(By.XPATH, "./div")[i]

        # Extract all information
        # Insert node
        # Click element to expand
        title_soup = BeautifulSoup(title.get_attribute("innerHTML"), features="html.parser")
        title_name_container = title_soup.find("div", class_="row")
        title_name_components = title_name_container.find_all("div")

        # Get title name formatted nicely
        title_name = title_name_components[1]
        title_chapters = title_name_components[2]
        node_name_add = get_text_clean(title_name)
        node_chapters_add = get_text_clean(title_chapters)
        node_name = f"{node_name_add} - {node_chapters_add}"
    
        
        node_level_classifier = "TITLE"
        node_type = "structure"
        url_add = title_soup.find("a").get("href")
        node_link = f"{node_link}{url_add}"
        node_number = node_link.split("#title")[-1]
        print(node_number)
        node_name = f"Title {node_number} - {node_name}"
        node_id = f"{title_node_parent}{node_level_classifier}={node_number}/"
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_parent, None, None, None, None, None)

        insert_node(node_data)
        chapter_node_parent = node_id
        

        link_container = title.find_element(By.TAG_NAME, "a")
        link_container.click()
        time.sleep(4)

        # Find the list of chapters
        # Iterate through each chapter
        # Call scrape_chapter() for each, don't add the node now
        find_chapters = url_add.split("#")[1]
        chapters_container = DRIVER.find_element(By.ID, find_chapters)
        chapters_soup = BeautifulSoup(chapters_container.get_attribute("innerHTML"), features="html.parser")
        chapters = chapters_soup.find_all("a")
        for chapter in chapters:
            url = BASE_URL + chapter['href']
            scrape_chapter(url, top_level_title, chapter_node_parent)


    



def scrape_chapter(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors="ignore") # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    print(node_parent)

    # Find chapter information, add the chapter
    # Iterate over every section
    # call scrape_section() for each url, don't add section now
    chapter_name = soup.find("h2", id="skipTo")
    node_name = get_text_clean(chapter_name)
    node_level_classifier = "CHAPTER"
    node_type = "structure"
    node_link = url
    chap_node_number = node_name.split(" ")[1].rstrip(":")
    node_id = f"{node_parent}{node_level_classifier}={chap_node_number}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)

    insert_node(node_data)

    sections_container = chapter_name.find_next_sibling("ul")

    sections = sections_container.find_all("a")

    for section in sections:
        url = BASE_URL + section['href']
        scrape_section(url, top_level_title, node_id, chap_node_number)

    

    

def scrape_section(url, top_level_title, node_parent, chap_node_number):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors="ignore") # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    # Find section information, add the section

    section_name = soup.find("h2", id="skipTo")
    node_name = get_text_clean(section_name)
    node_level_classifier = "SECTION"
    node_type = "content"
    node_link = url
    node_number = node_name.split(" ")[1].rstrip(":")
    node_id = f"{node_parent}{node_level_classifier}={node_number}"




    node_text = []
    node_addendum = None
    node_references = None
    node_tags = {}

    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            break

    if node_type != "reserved":
        section_texts = section_name.find_next_siblings("p")
        for section_text in section_texts:
            node_text.append(get_text_clean(section_text))
    else:
        node_text = None

    if node_tags == {}:
        node_tags = None
    
    node_citation = f"Mass. Gen. Laws Chapter {chap_node_number}, § {node_number} "
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_allow_duplicate(node_data)


    


# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ma/",
        None,
        "jurisdiction",
        "STATE",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    corpus_row_data = (
        "ma/statutes/",
        None,
        "corpus",
        "CORPUS",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "ma/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_skip_duplicate(jurisdiction_row_data)
    insert_node_skip_duplicate(corpus_row_data)

def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, temp9, node_tags = row_data
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)

    base_node_id = node_id
    
    for i in range(2, 10):
        try:
            insert_node(node_data)
            if verbose:
                print(node_id)
            break
        except Exception as e:
            if verbose:
             print(f"** Inside insert_node_allow_duplicate, ignoring the error: {e}")
            node_id = base_node_id + f"-v{i}"
            if "structure" in node_type:
                node_id += "/"
                node_type = "structure_duplicate"
            elif "reserved" in node_type:
                node_type = "reserved_duplicate"
            else:      
                node_type = "content_duplicate"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        continue

def insert_node_skip_duplicate(row_data, verbose=True):
    """
    Insert a node, but skip it if it already exists. Returns True if skipped, False if inserted.
    """
    node_id = row_data[0]
    try:
        insert_node(row_data)
        if verbose:
            print(node_id)
        return False
    except:
        if verbose:
            print("** Inside insert_node_skip_duplicate, skipping:",node_id)

        return True
    


def get_text_clean(element):
    text = element.get_text().replace('\xa0', '').replace('\r', ' ').replace('\n', '').strip()
    text = re.sub(r'\s+', ' ', text)
    return text
if __name__ == "__main__":
    main()