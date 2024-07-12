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



# Replacle with the state/country code
JURISDICTION = "hi"
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will2"
# Don't include last / in BASE_URL
TOC_URL = "https://www.capitol.hawaii.gov/docs/hrs.htm"
BASE_URL = "https://www.capitol.hawaii.gov"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["REPEALED", "Repealed"]

CHAPTER_PARENT = None
TOP_LEVEL_TITLE = 0

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            try:
                scrape_chapter(url)
            except:
                continue
    

def scrape_chapter(url):
    global CHAPTER_PARENT

    #print(f"=== Scrape_chapter ===\n {url}")
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(.25)
   
    
    soup = BeautifulSoup(DRIVER.page_source, features="html.parser")


    p_tags = soup.find_all('p')

    # Extract the structure nodes, Division or Title
    node_parent = None
    skipNext = False
    for p in p_tags:
        txt = get_text_clean(p)
        
        if "Chapter" in txt or "CHAPTER" in txt or "Subtitle" in txt or "SUBTITLE" in txt:
            break
        if txt == "":
            continue
        if "DIVISION" in txt:
            continue

        if skipNext:
            skipNext = False
            continue
         
        skip, skipNext, node_parent = extract_and_insert_level(url, p)
        CHAPTER_PARENT = node_parent
        if skip:
            return
        

        
        
    #print(f"CHAPTER_PARENT: {CHAPTER_PARENT}")

    # Find the start of sections
    section_start_index = -1
    node_type = "structure"
    for i, p in enumerate(p_tags):
        node_type = "structure"
        txt = get_text_clean(p)
        if txt == "Section" or "Part " in txt[0:10]:
            section_start_index = i
            break
        # Chapter itself is repealed
        if "REPEALED" in txt:
            node_type = "reserved"
            node_number_temp = url.split("/")[-1].split(".")[0].split("_")[-1].replace("000", "").replace("00", "").replace("-", "")
            chapter_name = f"Chapter {node_number_temp} REPEALED"

            break
    #print(f"section_start_index: {section_start_index}")
    node_parent = CHAPTER_PARENT
    if node_type != "reserved":
        # Extract the chapters/subtitles
        subtitle_name = None
        chapter_name = None
        possible_node_name = ""
        for i in range(section_start_index-2, -1, -1):
            #print(i)
            p_element = p_tags[i]
            
            if p_element['class'][0] == "XNotes":
                print("Found XNotes, breaking.")
                break
            if p_element.find("a"):
                print("Found a section link, breaking.")
                break
            txt = get_text_clean(p_element)
            #print(txt)
            possible_node_name = txt + " " + possible_node_name
            if "CHAPTER" in txt or "Chapter" in txt:
                # Found second chapter, add as reserved
                #print("Chapter name: ", chapter_name)
                if chapter_name is not None:
                    print("Reserved chapter found")
                    reserved_chapter_name = possible_node_name
                    reserved_chapter_num = reserved_chapter_name.split(" ")[1]
                    reserved_chap_node_data = (f"{node_parent}CHAPTER={reserved_chapter_num}/", TOP_LEVEL_TITLE, "reserved", "CHAPTER", None, None, None, url, None, reserved_chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    skip_reserved_chapter = insert_node_skip_duplicate(reserved_chap_node_data)
                    break
                #print("Found chapter")
                chapter_name = possible_node_name
                possible_node_name = ""
            if "SUBTITLE" in txt:
                subtitle_name = possible_node_name
                possible_node_name = ""

            
        
        
        node_type = "structure"
        # Possibly insert a subtitle
        if subtitle_name:
            node_level_classifier = "SUBTITLE"
            
            node_name = subtitle_name
            node_number = subtitle_name.split(" ")[1]
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            subtitle_node_id = f"{CHAPTER_PARENT}{node_level_classifier}={node_number}/"
            node_link = url
            node_data = (subtitle_node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, CHAPTER_PARENT, None, None, None, None, None)
            node_parent = subtitle_node_id

            skip_subtitle = insert_node_skip_duplicate(node_data)
            
        
    
    #print(f"chapter_name: {chapter_name}")
        
    # Always insert a chapter
    node_level_classifier = "CHAPTER"
    node_name = chapter_name
    node_number = chapter_name.split(" ")[1]
    if node_number[-1] == "." or node_number[-1] == "]":
        node_number = node_number[:-1]
    node_id = f"{node_parent}{node_level_classifier}={node_number}/"
    node_link = url
    node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    node_parent = node_id
    real_parent = node_id
    skip_chapter = insert_node_skip_duplicate(node_data)

    if skip_chapter:   
        return
    if node_type == "reserved":
        return
    
    

    for i, p in enumerate(p_tags):
        if i < section_start_index:
            continue
        txt = get_text_clean(p)
        #print(f"i: {i}, extraction txt: {txt}")
        # Structure Node
        if p.find("a") is None:
            # Case 1: Add a structure node
            if "Part" in txt[0:10]:
                node_name = txt
                node_number = node_name.split(" ")[1]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]

                node_level_classifier = "PART"
                node_link = url
                node_id = f"{real_parent}{node_level_classifier}={node_number}/"
                node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                node_parent = node_id
                skip = insert_node_skip_duplicate(node_data)
                
                continue
            # Case 2: Skipping "Section" header
            elif "Section" in txt:
                #print("Skipping Section header")
                continue
            # Skipping empty format lines
            else:
                #print("Skipping empty format line")
                continue
        link_container = None
        for a_tag in p.find_all("a"):
            if 'href' in a_tag.attrs:
                link_container = a_tag
                break
        
        node_citation = get_text_clean(link_container).replace(",", "")
        node_number = node_citation.split("-")[-1]
        
        ### Checking if a node is reserved
        for word in RESERVED_KEYWORDS:
            if word in txt:
                node_type = "reserved"
                break
        if node_type == "reserved":
            reserved_node_id = f"{node_parent}SECTION={node_number}"
            reserved_node_level_classifier = "SECTION"
            reserved_node_link = url
            if 'href' in link_container.attrs:
                reserved_node_link = BASE_URL + link_container['href']
            reserved_node_data = (reserved_node_id, TOP_LEVEL_TITLE, node_type, reserved_node_level_classifier, None, None, None, reserved_node_link, None, txt, None, None, None, None, None, node_parent, None, None, None, None, None)

            insert_node_allow_duplicate(reserved_node_data)
            node_type = "content"
            continue
        #print(link_container.attrs)

        node_link = BASE_URL + link_container['href']
        try:
            scrape_section(node_link, node_parent)
        except:
            pass


# Division 1. Government
# 1 - 21
# Division 2. Business
# 22 - 27
# Division 3. Property; Family
# 28 - 31
# Division 4. Courts and Judicial Proceedings
# 32 - 36
# Division 5. Crimes and Criminal Proceedings
# 37 - 41

def extract_and_insert_level(url, level_container):
    #print("=== Extract_and_insert_level ===")
    global TOP_LEVEL_TITLE
    skipNext = False
    try:
        node_name1 = get_text_clean(level_container)
        #print(f"node_name1: {node_name1}")
        node_name_2 = get_text_clean(level_container.next_sibling.next_sibling)
        if node_name_2.strip() != "":
            skipNext = True
        #print(f"node_name_2: {node_name_2}")
        node_name = node_name1 + " " + node_name_2
        node_link = url
        node_type = "structure"
        node_number = node_name.split(" ")[1]
        if node_number[-1] == ".":
            node_number = node_number[:-1]
    except:
        return True, False,  None
    

    node_parent = f"hi/statutes/DIVISION={TOP_LEVEL_TITLE}/"

    if node_number == "1":
        node_parent = "hi/statutes/DIVISION=1/"
        node_data = ("hi/statutes/DIVISION=1/", "1", node_type, "DIVISION", None, None, None, node_link, None, "Division 1. Government", None, None, None, None, None, "hi/statutes/", None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        TOP_LEVEL_TITLE = "1"
        
    elif node_number == "22" or node_number == "27":
        node_parent = "hi/statutes/DIVISION=2/"
        node_data = (node_parent, "2", node_type, "DIVISION", None, None, None, node_link, None, "Division 3. Property; Family", None, None, None, None, None, "hi/statutes/", None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        TOP_LEVEL_TITLE = "2"
    elif node_number == "28":
        node_parent = "hi/statutes/DIVISION=3/"
        node_data = (node_parent, "3", node_type, "DIVISION", None, None, None, node_link, None, node_name, None, None, None, None, None, "hi/statutes/", None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        TOP_LEVEL_TITLE = "3"
    
    elif node_number == "32":
        node_parent = "hi/statutes/DIVISION=4/"
        node_data = (node_parent, "4", node_type, "DIVISION", None, None, None, node_link, None, node_name, None, None, None, None, None, "hi/statutes/", None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        TOP_LEVEL_TITLE = "4"
    elif node_number == "37":
        node_parent = "hi/statutes/DIVISION=5/"
        node_data = (node_parent, "5", node_type, "DIVISION", None, None, None, node_link, None, node_name, None, None, None, None, None, "hi/statutes/", None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        TOP_LEVEL_TITLE = "5"

    node_level_classifier = node_name.split(" ")[0].upper()
    node_id = f"{node_parent}{node_level_classifier}={node_number}/"
    node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
     ## INSERT STRUCTURE NODE, if it's already there, skip it
    skip = insert_node_skip_duplicate(node_data)
    return skip, skipNext, node_id
        


def scrape_section(url, node_parent):
    DRIVER = webdriver.Chrome()
    DRIVER.get(url)
    DRIVER.implicitly_wait(.25)
    
    real_parent = node_parent
    soup = BeautifulSoup(DRIVER.page_source, features="html.parser")

    node_type = "content"
    node_level_classifier = "SECTION"

    # Before getting node_text, initialize defaults
    node_addendum = None
    node_text = []
    node_tags = {}
    node_references = {}
    internal = []
    external = []
    indentation = [] # Optional


    all_a_tags = soup.find_all("a")
    for a_tag in all_a_tags:
        if 'href' in a_tag.attrs:
            href = a_tag['href']
            if href == 'https://www.capitol.hawaii.gov/help.aspx':
                return
    # Don't get node_text for reserved nodes
    all_p_tags = soup.find_all("p")
    category = None
    #print(len(all_p_tags))
    empty_node_name = True
    #print("=== Inside scrape section enumerate === \n")
    for i, p in enumerate(all_p_tags):
        txt = get_text_clean(p)
        
        #print(f"i: {i}, txt: {txt}")
        if txt == "":
            continue
        if "PART " in txt[0:10]:
            continue

        if p.find("b") and empty_node_name:
            #print("Found bold")
            bold = p.find("b")
            print(f"bold: {bold}")

            node_name = txt
            # if len(p.find_all("b")) > 1:
            #     node_name += get_text_clean(bold.next_sibling) + " "
            #     print(node_name)
            #     node_name += get_text_clean(p.find_all("b")[-1]) 
            #     print(node_name)
            
            node_name = node_name.replace("[", "").replace("]", "").strip()
            node_name = node_name.replace("- ", "-")
            print(f"replaced node_name: {node_name}")
            last_b = p.find_all("b")[-1]
            if get_text_clean(last_b) == "":
                last_b = bold
            # Extract the last word in the last b tag
            last_b_text = get_text_clean(last_b).replace("[", "").replace("]", "").replace("- ", "-").strip()
            print(f"last_b_text: {last_b_text}")
            last_b_last_word = last_b_text.split(" ")[-1]
            print(f"last_b_last_word: {last_b_last_word}")

            # Find the index of last_b_last_word in node_name
            index = node_name.find(last_b_last_word)
            print(f"Index of last_b_last_word: {index}")
            # Remove everything after index+len(last_b)
            node_name = node_name[:index+len(last_b_last_word)]
            #print(f"node_name: {node_name}")
            node_citation = node_name.split(" ")[0]

            node_number = node_citation.split("-")[-1]
            #print(f"node_number: {node_number}")
            empty_node_name = False
            #### Checking if a node is reserved
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved"
                    break
            if node_type == "reserved":
                break
    
        
        
        for a_tag in p.find_all("a"):
            if 'href' not in a_tag.attrs:
                continue
            href = a_tag['href']
            ref_url = url + "#" + href
            internal.append({"citation": href, "link": ref_url, "text": txt})
        
        #print(p.attrs)
        if p['class'][0] == "XNotesHeading":
            category = txt
        elif p['class'][0] == "XNotes":
            if category not in node_tags:
                node_tags[category] = []
            node_tags[category].append(txt)
        else:
            node_text.append(txt)

    node_id = f"{node_parent}SECTION={node_number}"
    node_citation = f"HRS {node_citation}"
    node_link = url
    # Find any text within [ and ] in node_text[-1]
    node_addendum = None
    if node_text and "[" in node_text[-1] and "]" in node_text[-1]:
        node_addendum = node_text[-1].split("[")[1].split("]")[0]
        

     # Construct node_tags, or set to None
    if len(indentation) > 0:
        node_tags['indentation'] = indentation
    if node_tags != {}:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None

    # Construct node_references, or set to None
    if len(internal) > 0:
        node_references['internal'] = internal
    if len(external) > 0:
        node_references['external'] = external
    if node_references != {}:
        node_references = json.dumps(node_references)
    else:
        node_references = None

    if len(node_text) == 0:
        node_text = None

    
    ### FOR ADDING A CONTENT NODE, allowing duplicates
    node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_allow_duplicate(node_data)


    

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
        if verbose:
            print(f"** Inside insert_node_ignore_duplicate, ignoring the error: {e}")
    return

def insert_node_allow_duplicate(row_data, verbose=True):
    node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, node_text, temp1, node_citation, node_link, node_addendum, node_name, temp2, temp3, temp4, temp5, temp6, node_parent, temp7, temp8, node_references, temp9, node_tags = row_data
    node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)

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
            if node_type != "content":
                node_id += "/"
                node_type = "structure_duplicate"
            else:      
                node_type = "content_duplicate"
            node_data = (node_id, TOP_LEVEL_TITLE, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
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
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ').strip()
    
    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)
    return clean_text

if __name__ == "__main__":
    main()
