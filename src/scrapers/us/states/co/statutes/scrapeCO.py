import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
import re
from bs4.element import Tag
import docx2txt
import json
from node import Node

# Replacle with the state/country code
JURISDICTION = "co"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_node"
 = "will2"
# Don't include last / in BASE_URL
TOC_URL = "Link to table of contents"
BASE_URL = "basic link"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["(Repealed)"]


# Title, Category, Article, Part, Section


def main():
    insert_jurisdiction_and_corpus_node()
    #crs2023-title-01.docx
    for i in range(1, 45):
        # Adding 1 leading 0 to single digit numbers
        if i < 10:
            title_number = f"0{i}"
        else:
            title_number = str(i)
        filename = f"{DIR}/data/crs2023-title-{title_number}.docx"
        scrape_per_title(filename, str(i))

    

def scrape_per_title(filename, top_level_title):
    text = docx2txt.process(filename)
    title_index = text.find("TITLE ")

    # Find the
    og_parent = "co/statutes/"
    text = text[title_index:]
    
    chunk_split = text.split("\n\n\n\n\t")


    found_title = False
    found_article = False
    found_part = False

    current_node = None
    part_node_id = None
    article_node_id = None
    for i, line in enumerate(chunk_split):
        print(i)
        print(repr(line))
        if i == 20:
            exit(1)
        

        # Structure node case
        node_type = "structure"
        # TITLE case
        if line[0:5] == "TITLE":
            current_node = Node(None, og_parent, top_level_title, "structure", "TITLE", node_name=line.replace("\t", "").strip())
            found_title = True
            continue

        # TITLE Followup Case
        if found_title:
            current_node.node_name += line.replace("\t", "").strip()
            title_node_id = f"{og_parent}{current_node.node_level_classifier}={top_level_title}/"
            current_node.node_id = title_node_id
            found_title = False
            continue


        # ARTICLE Case
        if line[0:7] == "\tARTICLE":
            dumb_insert(current_node)
            node_name = line.replace("\t", "").strip()
            node_level_classifier = "ARTICLE"
            found_article = True
            current_node = Node(None, title_node_id, top_level_title, "structure", node_level_classifier, node_name=node_name)
            continue
        # ARTICLE Followup Case
        if found_article:
            current_node.node_name += line.replace("\t", "").strip()
            node_number = node_name.split(" ")[1]
            article_node_id = f"{category_node_id}{current_node.node_level_classifier}={node_number}/"
            current_node.node_id = article_node_id
            found_article = False
            continue


        # PART CASE
        if line[0:5] == "\tPART":
            dumb_insert(current_node)
            node_name = line.replace("\t", "").replace("\n", "").strip()
            node_level_classifier = "PART"
            found_part = True
            current_node = Node(None, article_node_id, top_level_title, "structure", node_level_classifier, node_name=node_name)
            continue
        # PART FOLLOWUP CASE
        if found_part:
            current_node.node_name += line.replace("\t", "").strip()
            node_number = node_name.split(" ")[1]
            part_node_id = f"{article_node_id}{current_node.node_level_classifier}={node_number}/"
            current_node.node_id = part_node_id 
            found_part = False
            continue
        # CATEGORY CASE
        if line[0] == "\t":
            print(repr(line))
            
            dumb_insert(current_node)
            node_name = line.replace("\t", "").replace("\n", "").strip()
            node_level_classifier = "CATEGORY"
            category_node_id = f"{title_node_id}{node_level_classifier}={node_name.replace(' ', '-')}/"
            current_node = Node(category_node_id, title_node_id, top_level_title, "structure", node_level_classifier, node_name=node_name)
            continue
        
        if part_node_id is None:
            node_parent = article_node_id
        else:
            node_parent = part_node_id
        # Section case
        if line[0:len(top_level_title)+1] == f"{top_level_title}-":
            dumb_insert(current_node)
            # Find index of second occurence of "."
            index = line.find(".", line.find(".") + 1)
            node_name = line[0:index+1]
            node_citation = node_name.split(".")[0]
            node_number = node_citation.split("-")[-1]
            node_level_classifier = "SECTION"
            node_number = node_name.split(" ")[0]
            section_node_id = f"{part_node_id}{node_level_classifier}={node_number}/"
            
            node_text = []
            all_node_text = line.split("\n\n\t")
            for txt in all_node_text:
                node_text.append(txt.replace("\t", " "))

            current_node = Node(section_node_id, node_parent, top_level_title, "content", node_level_classifier, node_text=None, node_citation=node_citation, node_link=None, node_addendum=None, node_name=node_name)
            continue
                        
        
        # Addendum
        if line[0:7] == "Source:":
            current_node.node_addendum = line
            continue

        # Cross References
        if line[0:15] == "Cross references:":
            current_node.node_references = {'cross references': [line]}
            continue

        if current_node.node_tags is None:
            current_node.node_tags = {}
        current_node.node_tags[line.split(":")[0]] = line.split(":")[1]



        




        
       
    

    
    #title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    #insert_node_ignore_duplicate(node_data)
    


def scrape_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")



    #### Extract content_node information 
    # node_name = ""
    # node_number = ""
    # node_level_classifier = "SECTION"
    # node_link = ""
    # node_citation = ""

    # node_id = f"{node_parent}{node_level_classifier}={node_number}"
    

    #### Checking if a content node is reserved
    # node_type = "content"
    # node_tags = {}
    # for word in RESERVED_KEYWORDS:
    #     if word in node_name:
    #         node_type = f"{structure}_reserved"
    #         node_tags['reserved_reason'] = word
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


    #### Construct node_tags
    # if len(indentation) > 0:
    #     node_tags['indentation'] = indentation
   
    #### Construct node_references
    # if len(internal) > 0:
    #     node_references['internal'] = internal
    # if len(external) > 0:
    #     node_references['external'] = external
    

    ### ADD A CONTENT NODE, allowing duplicates
    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # insert_node_allow_duplicate(node_data)
    



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


def dumb_insert(node):
    if node is not None:
        row_data = node.get()
        if node.node_level_classifier == "SECTION":
            insert_node_allow_duplicate(row_data)
        else:
            insert_node_skip_duplicate(row_data)
        
    
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



