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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from bs4.element import Tag


# Replacle with the state/country code
JURISDICTION = "sd"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "madeline"
# Don't include last / in BASE_URL
BASE_URL = "https://sdlegislature.gov"
TOC_URL = "https://sdlegislature.gov/Statutes"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["REPEALED", "Repealed ", "Superseded.", "Ommitted.", "Repealed by"]


def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_per_title(url)
    

def scrape_per_title(url):
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(10)
    og_parent = "sd/statutes/"


    # title_contianer = DRIVER.find_element(By.CLASS_NAME, "v-application--wrap")

    soup = BeautifulSoup(DRIVER.page_source, 'html.parser')

# Find the container <div>
    container_div = soup.find('div', {'class': 'col-sm-12 col-md-10 col'})
    levels = container_div.find_all("p")
    title_name = levels[0].text.strip()
    title_id = levels[1].text.strip()

    top_level_title = url.split("/")[-1]

    node_type = "structure"
    node_level_classifier = "TITLE"
    node_link = url
    node_name = f"{title_name} - {title_id}"

    node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"

    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
  


    for level in levels:
        if level == levels[0] or level == levels[1]:
            continue

        level_name = level.text.strip()

        if level_name == "Chapter":
            continue
        elif level.find("a") is None:
            continue

        level_url = level.find("a")
        url = level_url['href']
        print(url)
        scrape_per_chapter(url, top_level_title, node_id)


def scrape_per_chapter(url, top_level_title, node_parent):
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(10)
    wait = WebDriverWait(DRIVER, 10)
    layout_row_wrap = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "layout.row.wrap")))

    # Find the first div element following the 'layout row wrap' div
    # Note: You might need to adjust the XPath if this is not the exact structure
    container_div_xpath = "//div[contains(@class, 'layout row wrap')]/following-sibling::div[1]"

    container_div = DRIVER.find_element(By.XPATH, container_div_xpath)

    # Find all <p> elements with dir="ltr" within this div
    sections_divs = container_div.find_elements(By.XPATH, ".//p[@dir='ltr']")  

    # element = DRIVER.find_element(By.CLASS_NAME, "v-application--wrap")
    # DRIVER.execute_script("arguments[0].scrollIntoView();", element) 


    soup = BeautifulSoup(DRIVER.page_source, 'html.parser')

    # sections_divs = soup.find_all("p", dir="ltr")
  

    chapter_name = sections_divs[0].text.strip()
    chapter_name_add = sections_divs[1].text.strip()
    node_name = f"{chapter_name} - {chapter_name_add}"
    node_number = chapter_name.split("-")[-1]
    node_type = "structure"
    node_level_classifier = "CHAPTER"

    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            break
    
    node_id = f"{node_parent}{node_level_classifier}={node_number}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, url, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    section_node_parent = node_id

    first_class = sections_divs[3].get_attribute('class')
    for section in sections_divs:
        if section == sections_divs[0] or section == sections_divs[1] or section == sections_divs[2]:
            continue
        section_class = section.get_attribute('class')

        if section_class == first_class:
            section_html = section.get_attribute('outerHTML')
        
        # Parse with BeautifulSoup
            section = BeautifulSoup(section_html, 'html.parser')

            section_url = section.find("a")
            url = section_url['href']
            section_name = section.get_text().strip()
            print(section_name)
            node_number = section_url.get_text().strip()
            print(node_number)
            section_page_url = f"https://sdlegislature.gov/api/Statutes/{node_number}.html?all=true"
            for word in RESERVED_KEYWORDS:
                if word in section_name:
                    node_type = "reserved"
                    break
            if node_type != "reserved":
                
                scrape_per_section(section_page_url, top_level_title, section_node_parent, node_number)
            else:
                node_number = node_number.split("-")[-1].rstrip(".")
                node_id = f"{node_id}SECTION={node_number}"
                node_level_classifier = "SECTION"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, url, None, section_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                insert_node_allow_duplicate(node_data)
                node_type = "content"
        else: 
            return
            
    


def scrape_per_section(url, top_level_title, node_parent, node_number):
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(10)

    soup = BeautifulSoup(DRIVER.page_source, 'html.parser')

    section_container = soup.find("body")
    section_container_text = section_container.find("div")

    section_text = section_container_text.find_all("p", dir="ltr")

    section_name = section_text[0].text.strip()
    section_addendum = section_text[-1].text.strip()

    node_text = []

    for text in section_text: 
        if text == section_text[0] or text == section_text[-1]:
            continue
        else:
            text_add = text.get_text().strip()
            node_text.append(text_add)
    

    node_type = "content"
    node_level_classifier = "SECTION"
    node_link = url
    node_name = section_name

    citation_number = node_number
    node_number = citation_number.split("-")[-1].rstrip(".")
    node_citation = f"SDLC § {citation_number}"

    node_id = f"{node_parent}{node_level_classifier}={node_number}"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, section_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_allow_duplicate(node_data)




    



    

        

            


        


    #### Extract content_node information 
    # node_name = ""
    # node_number = ""
    # node_level_classifier = "SECTION"
    # node_link = ""
    # node_citation = ""

    # node_id = f"{node_parent}{node_level_classifier}={node_number}"
    # node_type = "content" # Default to content


    #### Checking if a node is reserved
    # for word in RESERVED_KEYWORDS:
    #     if word in node_name:
    #         node_type = "reserved"
    #         break


    #### Before getting node_text, initialize defaults
    # node_addendum = None
    # node_text = None
    # node_tags = {}
    # node_references = {}
    # internal = []
    # external = []
    # indentation = [] # Optional

    #### Don't get node_text for reserved nodes
    # if node_type != "reserved":
    #     node_text = []
    #     node_addendum = ""
    #     # Get node_text


    #### Construct node_tags, or set to None
    # if len(indentation) > 0:
    #     node_tags['indentation'] = indentation
    # if node_tags != {}:
    #     node_tags = json.dumps(node_tags)
    # else:
    #     node_tags = None

    #### Construct node_references, or set to None
    # if len(internal) > 0:
    #     node_references['internal'] = internal
    # if len(external) > 0:
    #     node_references['external'] = external
    # if node_references != {}:
    #     node_references = json.dumps(node_references)
    # else:
    #     node_references = None

    ### ADD A CONTENT NODE, allowing duplicates

    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # insert_node_allow_duplicate(node_data)
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        f"{JURISDICTION}/",
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
        f"{JURISDICTION}/statutes/",
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
        f"{JURISDICTION}/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)

def insert_node_ignore_duplicate(row_data, verbose=True):
    try:
        util.insert_row_to_local_db(, TABLE_NAME, row_data)
    except psycopg2.errors.UniqueViolation as e:
        print(f"** Inside insert_node_ignore_duplicate, ignoring the error: {e}")
    return

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
    



def get_text_clean(element, direct_children_only=False):
    '''
    Get text from BeautifulSoup element, clean it, and return it.
    element: BeautifulSoup element (Tag, NavigableString, etc.)
    direct_children_only: If True, only get the text from the direct children of the element
    '''
    if element is None:
        raise ValueError("==== Element is None in get_text_clean! ====")
    
    # Only allow the get_text() function if the element is a BS4 Tag
    if not isinstance(element, Tag):
        direct_children_only = True

    # Get all direct children text, the XML way
    if direct_children_only:
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    

    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)
    return clean_text

if __name__ == "__main__":
    main()