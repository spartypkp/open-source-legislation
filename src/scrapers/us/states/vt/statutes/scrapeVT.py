import json
import re
import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "madeline"
TABLE_NAME = "vt_node"
BASE_URL = "https://legislature.vermont.gov"
TOC_URL = "https://legislature.vermont.gov/statutes/"
SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
RESERVED_KEYWORDS = ["Repealed", "Expired", "Reserved"]

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            if ("title" in url):
                top_level_title = url.split("title/")[-1].strip()
                top_level_title = top_level_title.split("0")[-1]
                if ('APPENDIX' in top_level_title):
                    top_level_title = top_level_title.replace("APPENDIX", "-APPENDIX")
            scrape_per_title(url, top_level_title, "vt/statutes/")
            

def scrape_per_title(url, top_level_title, node_parent):
    
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    print(url)

    title_container = soup.find("div", id="main-content")
    title_name_tag = title_container.find("h2", class_="statute-title")
    title_node_name = title_name_tag.get_text().strip()
    node_number = top_level_title
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"{node_parent}TITLE={node_number}/"
    node_link = url
    node_text = None
    node_citation = None
    node_addendum = None
    print(node_id)
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, title_node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    # ADD title node_id to levels, or replace previous 
    

    scrape_level( url, top_level_title, node_id)
    

# Handles any generic structure node, routes sections to scrape_sections
def scrape_level(url, top_level_title, node_parent):
    print(url)
    base_node_parent_for_chapter = node_parent
    
    # Iterate over the container of the structure nodes
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text, features="html.parser")

    title_container = soup.find("div", id="main-content")
    div_elements = title_container.find_all("ul", recursive=False)

    if len(div_elements) == 1:
        next_level = div_elements[0].find_all("li", recursive=False)
    
        for level in next_level:
            
            a_tag = level.find("a")
            a_tag_text = a_tag.get_text().strip()
            if a_tag is None or a_tag_text == "":
                continue
            else:
                node_link = BASE_URL + a_tag["href"]
                node_name = a_tag.get_text().strip()
                print(node_name)
                if node_name == None:
                    continue
                if node_name.startswith("Chapter"):
                    node_level_classifier = "CHAPTER"
                elif node_name.startswith("Article"):
                    node_level_classifier = "ARTICLE"
                elif ("§" in node_name and "Repealed" in node_name):
                    node_level_classifier = "SECTION"
                    node_type = "reserved"
                    node_number = node_name.split(" ")[2].rstrip(':')
                    node_number = node_number.lstrip('0')
                    print(node_number)
                    if node_number == '':
                        node_number = node_name.split(" ")[1].rstrip(':')
                        node_number = node_number.lstrip('0')
                    
                    node_number = node_number.rstrip(',')
                    node_number = node_number.rstrip('.')
            
                    node_id = f"{node_parent}{node_level_classifier}={node_number}"
                
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)

                    # Check for reserved
                    try:
                        insert_node(node_data)
                        print(node_id)
                        continue  
                    except:
                        print("** Skipping:",node_id)
                        continue
                else:
                    scrape_sections(node_link, top_level_title, node_parent, node_name)
                    continue

                node_type = "structure"
                node_number = node_name.split(" ")[2].rstrip(':')
                node_number = node_number.lstrip('0')
                
                if node_number == '':
                    node_number = node_name.split(" ")[1].rstrip(':')
                    node_number = node_number.lstrip('0')
                
          
                node_id = f"{node_parent}{node_level_classifier}={node_number}/"
            
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)

                # Check for reserved
                for word in RESERVED_KEYWORDS:
                    if word in node_name:
                        node_type = "reserved"
                        break
                
                # Add the node or skip if already input
                try:
                    insert_node(node_data)
                    print(node_id)  
                except:
                    print("** Skipping:",node_id)
                    continue
       
                scrape_level(node_link, top_level_title, node_id)

    else:
        for div in div_elements:
            base_node_parent_for_chapter = base_node_parent_for_chapter
            next_level = div.find_all("li", recursive=False)
            for level in next_level:
                sub_level = level.find("strong")
                
                if sub_level:
                    node_name = sub_level.get_text().strip()
                    node_number = node_name.split(" ")[1].rstrip(':')
                    node_number = node_number.lstrip('0')
                    node_type = "structure"
                    node_level_classifier = node_name.split(" ")[0].upper()
                    # Construct node_id using the base node parent for the chapter
                    node_id = f"{base_node_parent_for_chapter}{node_level_classifier}={node_number}/"
                    node_link = url
                    next_level_node_parent = node_id
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, base_node_parent_for_chapter, None, None, None, None, None)
                    if "Repealed" in node_name:
                        node_type = "reserved"
                        # Use the base node parent for the chapter
                        node_parent = base_node_parent_for_chapter
                        next_level_node_parent = node_id
                        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                        try:
                            insert_node(node_data)
                            continue
                        except:
                            continue
                    try:
                        insert_node(node_data)
                    except:
                        continue
                    next_level_node_parent = node_id
                    
                    # Update the base node parent for the chapter
                else: 
                    a_tag = level.find("a")
                    section_node_parent = node_id
                    
                    if a_tag is None:
                        continue
                    elif "Repealed" in a_tag.get_text().strip():
                        node_type = "reserved"
                        # Use the base node parent for the chapter
                        node_parent = next_level_node_parent
                        node_name = a_tag.get_text().strip()
                        node_number = node_name.split(" ")[2].rstrip('.')
                        if node_number == '':
                            node_number = node_name.split(" ")[1].rstrip('.')
                        node_level_classifier = "SECTION"
                        repealed_node_id = f"{next_level_node_parent}SECTION={node_number}"
                        node_link = BASE_URL + a_tag["href"]
                        node_data = (repealed_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                        try:
                            insert_node(node_data)
                        except:
                            continue
                    else:
                        node_link = BASE_URL + a_tag["href"]
                        # Use the base node parent for the chapter
                        scrape_sections(node_link, top_level_title, section_node_parent, node_name)




def scrape_sections(node_link, top_level_title, node_parent, app_node_name):
    # Scrape a section regularly
    response = urllib.request.urlopen(node_link)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text, features="html.parser")
    print(node_link)

    section_container = soup.find("ul", class_="item-list statutes-detail")
    section_header = section_container.find("b")
    node_name = section_header.get_text().strip()
    print("this is node_name: " + node_name)

    if ("@ App. " in app_node_name):
        node_name = app_node_name
        print(app_node_name)
        node_number = node_name.split(" ")
        print("this is node_number split: ", node_number)
        node_number = node_number[3].rstrip('.')
    else:
        node_number = node_name.split(" ")[1]
        node_number = node_number.replace(",", "-").rstrip(".")
        
    node_type = "content"
    node_level_classifier = "SECTION"
    node_id = f"{node_parent}{node_level_classifier}={node_number}"
    print(node_number)
    print(node_id)
    

    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            node_name = node_name.replace(" ", "-")
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            break
    
    node_text = []
    node_citation = f"{top_level_title} V.S.A. § {node_number}"

    # Finding addendum
    node_addendum = ""
    node_tags = {}
    addendum_references = []

    section_container_content = section_container.find_all("p")


    if node_type != "reserved":
        section_container_content = section_container.find_all("p")
        for p in section_container_content:
            # Skip the sectionHead
            header = p.find("b")
            blank = p.get_text().strip() == ""
            if header:
                continue
            elif blank:
                continue
            
            temp = p.get_text().strip()
            text = temp.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').strip()
            text = re.sub(r'\s+', ' ', text) 

            node_text.append(text)

            

            # Defining pattern for the addendum text, which starts with "(Added" and ends with a closing parenthesis ")"
            addendum_pattern = re.compile(r'\(Added.*')
            addendum_pattern2 = re.compile(r'\(Amended.*')
            for i, text in enumerate(node_text):
    #            Find the addendum
                match = addendum_pattern.search(text)
                match2 = addendum_pattern2.search(text)
                if match:
                    addendum_text = match.group()
                    node_addendum = addendum_text
                    # Remove the addendum text from the entry
                    text_without_addendum = addendum_pattern.sub('', text).strip()
                    # Update the entry in node_text
                    node_text[i] = text_without_addendum

                elif match2: 
                    addendum_text = match2.group()
                    node_addendum = addendum_text
                    # Remove the addendum text from the entry
                    text_without_addendum = addendum_pattern.sub('', text).strip()
                    # Update the entry in node_text
                    node_text[i] = text_without_addendum
            
        
    if addendum_references != []:
        node_tags["addendum_references"] = addendum_references
        
    if node_tags != {}:
        node_tags = json.dumps(node_tags)
    else:
        node_tags = None


    node_references = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    base_node_id = node_id
    
    
    for i in range(2, 10):
        try:
            insert_node(node_data)
            print(node_id)
            
            break
        except Exception as e:   
            print(e)
            node_id = base_node_id + f"-v{i}"
            node_type = "content_duplicate"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        continue

    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "vt/",
        None,
        "jurisdiction",
        "FEDERAL",
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
        "vt/statutes/",
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
        "vt/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)




    
if __name__ == "__main__":
    main()