import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
import re
from bs4.element import Tag
from node import Node
import time

import json

# Replacle with the state/country code
JURISDICTION = "pa"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will"
# Don't include last / in BASE_URL
TOC_URL = "https://www.legis.state.pa.us/cfdocs/legis/CH/Public/pcde_index.cfm"
BASE_URL = "https://www.pacodeandbulletin.gov/"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 12
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["[Reserved]"]


def main():
    insert_jurisdiction_and_corpus_node()
    scrape_titles()
    
    

def scrape_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, "lxml")

    titles_container = soup.find(class_="DataTable")
    og_parent = f"{JURISDICTION}/statutes/"
    for i, title in enumerate(titles_container.tbody.find_all("tr")):
        if i < SKIP_TITLE:
            continue
        all_tds = title.find_all("td")
        top_level_title = get_text_clean(all_tds[0])
        node_name = get_text_clean(all_tds[1])
        
        node_link = all_tds[3].find("a")['href']
        node_type = "structure"
        node_level_classifier = "TITLE"
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"

        current_node = Node(node_id, og_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
        title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(title_node_data)
        scrape_level(node_link, top_level_title, current_node)
    

def scrape_level(url, top_level_title, node_parent):
    #print(url)
    title_schema = ["TITLE", "PART", "SUBPART", "ARTICLE", "DIVISION", "CHAPTER"]
    current_node = node_parent

    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, "lxml")
    
    
    soup = soup.find(id="pacode-text")
    levels_container = soup.find(id="pacode-text-window")
    blockquote = levels_container.find("blockquote")
    
    remove_all_br_tags(blockquote, verbose=True)
    

    
    for i, element in enumerate(blockquote.find_all("font")):
        if 'size' not in element.attrs or element.attrs['size'] != '+1':
            continue
        
        
        node_name = get_text_clean(element)
        node_number = node_name.split(" ")[1].strip()
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        
        node_level_classifier = node_name.split(" ")[0].upper()
        if node_level_classifier == "APPENDIX":
            continue

        # Make plural classifiers into singular
        if node_level_classifier[-1] == "S":
            node_level_classifier = node_level_classifier[:-1]
        try:
            node_link = "https://www.pacodeandbulletin.gov/Display/" + element.find("a")['href']
        except:
            node_link = url
        
        node_type = "structure"

    
        # Handle all content nodes first
        
        
        currentRank = title_schema.index(current_node.node_level_classifier)
        #print(f"Current: {currentRank}")
        
        newRank = title_schema.index(node_level_classifier)
        #print(f"New: {newRank}")
        
    
                # Determine the position of the newNode in the hierarchy
        if (newRank <= currentRank):
            temp_node = current_node

            while (title_schema.index(temp_node.node_level_classifier) > newRank):
                temp_node = temp_node.node_parent
                if (temp_node.node_level_classifier == 'TITLE'):
                    break
                
            
            current_node = temp_node
            currentRank = title_schema.index(current_node.node_level_classifier)
            # Set the ID of the newNode and add it to the current_node's children or siblings
            if (newRank == currentRank):
                if (not current_node.node_parent):
                    print("current_node.parent undefined!")
                    exit(1)

            
                node_parent = current_node.node_parent
                node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
                
                
                
                
                current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
            else:
                
                node_parent = current_node
                node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
                
                current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
            

            
        else:
            # Set the ID of the newNode and add it to the current_node's children
            node_id = f"{current_node.node_id}{node_level_classifier}={node_number}/"
            
            node_parent = current_node
            current_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_link=node_link, node_name=node_name)
        
        print(current_node.node_id)
        for word in RESERVED_KEYWORDS:
            if word in current_node.node_name:
                node_type = "reserved"
                break
        current_node_data = current_node.get()
        skip = insert_node_skip_duplicate(current_node_data)
        if skip:
            continue
        if node_level_classifier == "CHAPTER" and node_type != "reserved":
            print("Scraping sections")
            scrape_sections(node_link, top_level_title, node_id)




def scrape_sections(url, top_level_title, node_parent):
    #print(url)
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, "lxml")
    soup = soup.find(id="pacode-text")
    sections_container = soup.find(id="pacode-text-window")

    found_subchapter = False
    for link in sections_container.find_all("a"):
        if "href" in link.attrs and "subchap" in link['href']:
            found_subchapter = True
            node_name = get_text_clean(link.parent)
            node_number = node_name.split(" ")[0].strip()
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            node_level_classifier = "SUBCHAPTER"
            node_type = "structure"
            node_id = f"{node_parent}{node_level_classifier}={node_number}/"
            node_name = "Subchapter " + node_name

            node_link = "https://www.pacodeandbulletin.gov/Display/" + link['href']
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            
            
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved_structure"
                    break
            skip = insert_node_skip_duplicate(node_data)
            if skip:
                continue
            if node_type != "reserved":
                scrape_sections(node_link, top_level_title, node_id)
        
    if found_subchapter:
        return

    blockquote = sections_container.find("blockquote")
    if blockquote is None:
        return
    
    
    remove_all_br_tags(blockquote)
    
    found_first_section = False
    node_name = None
    node_number = None
    node_link = None
    node_level_classifier = None
    node_type = None
    node_id = None
    node_text = None
    node_addendum = None
    node_citation = None

    blockquote.find(class_="pacode-disclaimer").decompose()


    for i, tag in enumerate(blockquote.find_all(recursive=False)):
        
        if not isinstance(tag, Tag):
            continue
        #print(tag.prettify())
        if tag.name == "h4":
            if not found_first_section:
                found_first_section = True
        
        if not found_first_section:
            continue
        txt = get_text_clean(tag)
        

        if tag.name == "h4":
            if node_id is not None:
                 ### Construct node_tags, or set to None
                if node_text == []:
                    node_text = None
                if node_addendum == "":
                    node_addendum = None
                if len(indentation) > 0:
                    node_tags['indentation'] = indentation
                if len(notes_of_decisions) > 0:
                    node_tags['notes_of_decisions'] = notes_of_decisions
                if node_tags != {}:
                    node_tags = json.dumps(node_tags)
                else:
                    node_tags = None

                ### Construct node_references, or set to None
                if len(internal) > 0:
                    node_references['internal'] = internal
                if len(external) > 0:
                    node_references['external'] = external
                if node_references != {}:
                    node_references = json.dumps(node_references)
                else:
                    node_references = None

                ## ADD A CONTENT NODE, allowing duplicates

                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
                #print(node_id)
                insert_node_allow_duplicate(node_data)


            node_name = txt
            
            node_number = get_text_clean(tag.font)
            node_link = url + "#" + node_number
            node_number = node_number[:-1].replace("§ ", "").strip()
            
            

            node_level_classifier = "SECTION"
            node_type = "content"
            if "[Reserved]" in node_name:
                node_type = "reserved"
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            node_citation = f"{top_level_title} Pa. Code § {node_number}"
            node_addendum = ""
            node_text = []
            node_tags = {}
            node_references = {}
            internal = []
            external = []
            indentation = [] # Optional
            notes_of_decisions = []
            addendum_found = False
            references_found = False
            notes = False
            continue


        if txt == "":
            continue
        #print(tag.name)
        #print(txt)
        

        
        if txt == "Source":
            addendum_found = True
            continue
        if addendum_found:
            node_addendum += txt
            addendum_found = False
            continue
        if txt == "Cross References":
            references_found = True
            continue
        if references_found:
            internal.append({"text": txt})
            references_found = False
            continue
        if txt == "Notes of Decisions":
            notes = True
            continue
        if notes:
            notes_of_decisions.append(txt)
            continue

        
        node_text.append(txt)

    if node_id is not None:
        ### Construct node_tags, or set to None
        if node_text == []:
            node_text = None
        if node_addendum == "":
            node_addendum = None
        if len(indentation) > 0:
            node_tags['indentation'] = indentation
        if len(notes_of_decisions) > 0:
            node_tags['notes_of_decisions'] = notes_of_decisions
        if node_tags != {}:
            node_tags = json.dumps(node_tags)
        else:
            node_tags = None

        ### Construct node_references, or set to None
        if len(internal) > 0:
            node_references['internal'] = internal
        if len(external) > 0:
            node_references['external'] = external
        if node_references != {}:
            node_references = json.dumps(node_references)
        else:
            node_references = None

        ## ADD A CONTENT NODE, allowing duplicates

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        #print(node_id)
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

