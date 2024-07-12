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
from selenium.webdriver.support.ui import Select
import re
import time
import json
from bs4.element import Tag



# Replacle with the state/country code
JURISDICTION = "md"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will"
# Don't include last / in BASE_URL
TOC_URL = "https://mgaleg.maryland.gov/mgawebsite/laws/statutes"
BASE_URL = "https://mgaleg.maryland.gov"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["REPEALED"]

def main():
    insert_jurisdiction_and_corpus_node()
    scrape_titles()
    

def scrape_titles():
    
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)
    og_parent = "md/statutes/"
    main_body = DRIVER.find_element(By.ID, "mainBody")
    
    articles_container = main_body.find_element(By.ID, "Articles")
    select_obj = Select(articles_container)
    for i, code in enumerate(articles_container.find_elements(By.TAG_NAME, "option")):
        val = code.get_attribute("value")
        if val is None or val == "":
            continue
        top_level_title = val
        node_name = get_text_clean(code)
        node_level_classifier = "ARTICLE"
        node_type = "structure"
        node_link = TOC_URL
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"

        code_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_skip_duplicate(code_node_data)
        select_obj.select_by_value(f"{top_level_title}")
        time.sleep(1)

        # Find all sections
        sections_container = main_body.find_element(By.ID, "Sections")
        inserted_titles = []
        for j, section in enumerate(sections_container.find_elements(By.TAG_NAME, "option")):
            #time.sleep(1)
            node_citation_raw = get_text_clean(section)
            #print(node_citation_raw)
            if node_citation_raw is None or node_citation_raw == "":
                continue
            
            all_structure_nodes = node_citation_raw.split("-")
            if len(all_structure_nodes) == 2:
                temp = all_structure_nodes[1]
                index = temp.find(".")
                add_after = ""
                if index != -1:
                    add_after = temp[index:]
                    temp = temp[0:index]
                    
                
                length = len(temp) - 2
                
                temp_subtitle = temp[0:length]
                #print(f"T: {temp_subtitle}")
                temp_section = temp[length:]
                new_list = [all_structure_nodes[0], temp_subtitle, temp_section+add_after]
                all_structure_nodes = new_list

            node_parent = node_id
            
            
            node_type = "structure"
            node_link = TOC_URL
            

           
            node_level_classifier = "TITLE"
            node_number = all_structure_nodes[0]
            title_node_id = f"{node_parent}{node_level_classifier}={node_number}/"
            if node_number not in inserted_titles:
                node_name = f"Title {node_number}"
                
                
                title_node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                insert_node_skip_duplicate(title_node_data)
                inserted_titles.append(node_number)

            node_level_classifier = "SUBTITLE"
            node_number = all_structure_nodes[1]
            node_name = f"Subtitle {node_number}"
            subtitle_node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
            
            subtitle_node_data = (subtitle_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
            insert_node_skip_duplicate(subtitle_node_data, verbose=False)


            # 
            section_node_link = f"https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article={top_level_title}&section={node_citation_raw}&enactments=false"

            
            
            response = urllib.request.urlopen(section_node_link)
            data = response.read()      # a `bytes` object
            text = data.decode('utf-8') # a `str`; 
            soup = BeautifulSoup(text, features="lxml")
            section_container = soup.find(id="StatuteText")
            remove_all_br_tags(section_container)
            #print(section_container.prettify())
            node_text = []
            node_citation = f"Md. Agriculture § {node_citation_raw}"
            node_addendum = None
            node_references = None
            node_tags = None
            node_level_classifier = "SECTION"
            node_type = "content"
            
            for element in section_container.contents:
                
                if isinstance(element, Tag):
                    
                    continue
                else:
                    txt = get_text_clean(element)
                    if txt == "":
                        continue
                    #print(txt)
                    if len(node_text) == 0:
                        node_name = txt
                    node_text.append(txt)
            #print(node_text)
            node_number = all_structure_nodes[-1]
            section_node_id = f"{subtitle_node_id}{node_level_classifier}={node_number}"
            section_node_data = (section_node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_node_link, node_addendum, node_name, None, None, None, None, None, subtitle_node_id, None, None, node_references, None, node_tags)
            insert_node_allow_duplicate(section_node_data)
            




    


def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, node_incoming_references, node_tags = row_data
    
    # Replace all "empty" values with None
    if node_references is not None and node_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None
    
    if node_incoming_references is not None and node_incoming_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    if node_tags is not None and node_tags:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None
    
    if node_text is not None and node_text == []:
        node_text = None
    if node_addendum is not None and node_addendum == "":
        node_addendum = None

    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)

    
    
    base_node_id = node_id
    
    for i in range(2, 10):
        try:
            insert_node(node_data)
            if verbose:
                print(node_id)
            break
        except psycopg2.errors.UniqueViolation as e:
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
    node_id, top_level_title, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, node_incoming_references, node_tags = row_data
    
    if node_references is not None and node_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None
    
    if node_incoming_references is not None and node_incoming_references:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    if node_tags is not None and node_tags:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None
    
    if node_text is not None and node_text == []:
        node_text = None
    if node_addendum is not None and node_addendum == "":
        node_addendum = None
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)



    try:
        insert_node(node_data)
        if verbose:
            print(node_id)
        return False
    except psycopg2.errors.UniqueViolation as e:
        if verbose:
            print(f"** ERROR Inside insert_node_skip_duplicate, {e}\n   - Skipping: {node_id}")

        return True


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
    insert_node_skip_duplicate(jurisdiction_row_data)
    insert_node_skip_duplicate(corpus_row_data)




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

def debug_soup_to_file(soup, filename=""):
    with open(f"{DIR}/data/debug_soup{filename}.txt", "w") as write_file:
        write_file.write(soup.prettify())
    write_file.close()
    return

def remove_all_br_tags(soup, verbose=False):
    num_unwrapped = 0
    num_decomposed = 0
    for br in soup.find_all('br'):
        length = len(br.find_all(recursive=False))
        
        if length >= 1:
            num_unwrapped += 1
            br.unwrap()
            
        else:
            num_decomposed += 1
            br.decompose()
    if verbose:
        print(f"== Nuking <br> Tags ==\nUnwrapped: {num_unwrapped}\nDecomposed: {num_decomposed}\n=====================")
    #soup.smooth()

if __name__ == "__main__":
    main()