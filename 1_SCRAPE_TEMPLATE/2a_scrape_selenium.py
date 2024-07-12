import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
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
JURISDICTION = "state code"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"

# Don't include last / in BASE_URL
TOC_URL = "Link to table of contents"
BASE_URL = "basic link"
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
    og_parent = "or/statutes/"
    
    
    
    
    
    
    # Scroll to element



    # 144 total containers
    for i in range(2, 144):

        #print(i)
        container = DRIVER.find_element(By.ID, "MSOZoneCell_WebPartWPQ8")
        titles_containers = container.find_elements(By.TAG_NAME, "tbody")
        title = titles_containers[i]
        DRIVER.execute_script("arguments[0].scrollIntoView();", title)
        
        title_soup = BeautifulSoup(title.get_attribute("innerHTML"), features="html.parser")

        

        #print(title_soup.prettify())
        node_name = title_soup.get_text().strip()
        #print(node_name)
        # Skip doing anything for volume
        if "Volume" not in node_name:
            # Handle chapters separately 
            if len(title_soup.find_all("a")) > 1:
                all_chapters = title_soup.find_all("tr", recursive=False)
                for i, chapter_container in enumerate(all_chapters):
                    time.sleep(2)
                    all_tds = chapter_container.find_all("td", recursive=False)
                    link_container = all_tds[0].find("a")
                    name_container = all_tds[1]


                    node_name_start = link_container.get_text().strip()
                    node_number_raw = node_name_start.split(" ")[1]
                    node_number = str(int(node_number_raw))
                    node_link = BASE_URL + link_container['href']

                    node_name_end = name_container.get_text().strip()
                    if node_name_end == "(Former Provisions)":
                        node_type = "reserved"
                    else:
                        node_type = "structure"
                    
                    node_name = f"{node_name_start} {node_name_end}"
                    

                    node_level_classifier = "CHAPTER"
                    node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
                    chapter_node_data =  (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
                    try:
                        #insert_node(chapter_node_data)
                        print(node_id)
                    except:
                        print("** Skipping:",node_id)
                        continue

                    if node_type != "reserved":
                        scrape_chapter(node_link, top_level_title, node_id, node_number)

                # Don't click any chapter links
                continue


            # Handle Titles 
            else:

                node_number_raw = node_name.split(":")[1].strip()
                node_number = node_number_raw.split(" ")[0]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]
                
                node_type = "structure"
                node_level_classifier = "TITLE"
                node_link = TOC_URL
                title_node_id = f"{og_parent}{node_level_classifier}={node_number}/"
                top_level_title = node_number

                node_data =  (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
                try:
                    #insert_node(node_data)
                    print(title_node_id)
                except:
                    print("** Skipping:",title_node_id)
                    continue




        
        link_container = title.find_element(By.TAG_NAME, "a")
        link_container.click()
        
        time.sleep(1)



def scrape_chapter(url, top_level_title, node_parent, chapter_num):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors="ignore") # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    

    all_sections = soup.find_all("b")
    for i, section_tag in enumerate(all_sections):
        
        node_name = get_text_clean(section_tag)
        
        node_number_raw = node_name.split(" ")[0]
        node_citation = f"ORS {node_number_raw}"
        node_number = str(int(node_number_raw.split(".")[1]))

        node_level_classifier = "SECTION"
        node_type = "content"
        node_link = url
        node_id = f"{node_parent}{node_level_classifier}={node_number}"

        node_text = None
        node_addendum = None
        node_references = None
        node_tags = {}

        if node_type != "reserved":
            node_text = []
            p_tag = section_tag.parent
            print(p_tag.prettify())
            node_text.append(get_text_clean(p_tag))
            p_tag = p_tag.next_sibling
            print(p_tag.prettify())
            while True:
                txt = get_text_clean(p_tag)
                # Bold element found, investigate
                if p_tag.find("b") is not None:
                    b_txt = p_tag.find("b").get_text().strip()
                    # New section found, break
                    if b_txt[0:2] == "9.":
                        break
                    # Weird bold part of current section
                    node_tags[b_txt] = txt
                    p_tag = p_tag.next_sibling
                    continue
                
                
                node_text.append(txt)
                p_tag = p_tag.next_sibling

            
            possible_addendum = node_text[-1]
            # Find any text within [] and set it as addendum
            if "[" in possible_addendum and "]" in possible_addendum:
                node_addendum = possible_addendum.split("[")[1].split("]")[0]
        
        if node_tags != {}:
            node_tags = json.dumps(node_tags)
        else:
            node_tags = None
        
        ### FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        base_node_id = node_id
        
        for j in range(2, 10):
            try:
                #insert_node(node_data)
                print(node_id)
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{j}/"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue




    


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
    
    if node_text is not None and node_text:
        node_text = None
    if node_addendum is not None and node_addendum:
        node_addendum = None

    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)

    
    
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
    
    if node_text is not None and node_text:
        node_text = None
    if node_addendum is not None and node_addendum:
        node_addendum = None
    
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, node_incoming_references, node_tags)



    try:
        insert_node(node_data)
        if verbose:
            print(node_id)
        return False
    except:
        if verbose:
            print("** Inside insert_node_skip_duplicate, skipping:",node_id)

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
    soup.smooth()

if __name__ == "__main__":
    main()