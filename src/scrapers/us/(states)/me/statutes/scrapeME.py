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
TABLE_NAME = "me_node"
BASE_URL = "https://legislature.maine.gov/statutes"
TOC_URL = "https://legislature.maine.gov/statutes/"
RESERVED_KEYWORDS = ["REPEALED", "Expired", "Reserved"]
SKIP_TITLE = 39 # If you want to skip the first n titles, set this to n

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file, start=1):  # Start enumeration from 1
            # if i < 8:
            #     continue 
            if i < SKIP_TITLE:
                continue
  
            url = line
            if ("title" in url):
                parts = url.split('/')
                number_or_string_after_statutes = parts[parts.index('statutes') + 1] if 'statutes' in parts else None

                top_level_title = number_or_string_after_statutes
                top_level_title = top_level_title
                scrape_per_title(url, top_level_title, "me/statutes/")
            else:
                continue

## TITLE -> CHAPTER -> SECTION
## TITLE -> PART -> SUBPART -> CHAPTER -> SECTION
## TITLE -> PART -> CHAPTER -> SECTION
## TITLE -> PART -> CHAPTER -> SUBCHAPTER -> SECTION
## TITLE -> ARTICLE -> PART -> SECTION
## TITLE -> ARTICLE -> SECTION
## TITLE -> SUBTITLE -> CHAPTER -> SECTION
## TITLE -> SUBTITLE -> PART -> SECTION
            

def scrape_per_title(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text)


    title_container = soup.find("div", class_="title_toc MRSTitle_toclist col-sm-10")
    title_name = title_container.find("div", class_="title_heading")
    title_node_name = title_name.get_text()
    title_node_number = title_node_name.split(" ")
    title_node_number = title_node_number[1].replace(":","")
    top_level_title = title_node_number
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"{node_parent}TITLE={title_node_number}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, url, None, title_node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)
    node_parent = node_id
    # me/statutues/TITLE=1/


    div_elements = title_name.find_next_siblings("div")
    if len(div_elements) == 1:
            div_elements = div_elements[0].find_all(recursive=False)

    scrape_level(div_elements, url, top_level_title, node_id)
    

# Handles any generic structure node, routes sections to scrape_sections
def scrape_level(div_elements, url, top_level_title, node_parent):
    ## Finding different levels
    for i, div in enumerate(div_elements):
        class_list = div.get('class', [])

        node_type = "structure"
        all_headers = div.find("h2", recursive=False)

        # Guranteed structure node
        if all_headers is not None:
            # Extract structure node information
            # "Part I" + " " + "Administrative Agencies"
            node_name = all_headers.get_text().strip()
            node_type = "structure"
            node_level_classifier = node_name.split(" ")[0].upper()
            node_number = node_name.split(" ")[1].rstrip(":")
            node_link = url
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

            next_div_elements = div.find_all("div", recursive=False)
            if node_type != "reserved":
                scrape_level(next_div_elements, url, top_level_title, node_id)
        
        elif div.find("a") is not None:
            link_container = div.find("a")
            
            node_name = link_container.get_text().strip()

            if ("§" in node_name):
                url = BASE_URL + "/" + top_level_title + link_container['href'].replace("./", "/")
                
                node_name = node_name
                print(node_name)
                for word in RESERVED_KEYWORDS:
                    if word in node_name:
                        node_type = "reserved"
                        break
                if node_type != "reserved":
                    scrape_section(url, top_level_title, node_parent, node_name)
                    continue
                else:
                    node_type = "reserved"
                    node_level_classifier = "SECTION"
                    node_number = node_name.split(" ")[1].rstrip(".").replace("§","")
                    node_link = url
                    node_id = f"{node_parent}{node_level_classifier}={node_number}"

                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    try:
                        insert_node(node_data)
                        print(node_id)  
                        continue
                    except:
                        print("** Skipping:",node_id)
                        continue
            
            
            node_type = "structure"
            node_level_classifier = node_name.split(" ")[0].upper()
            node_number = node_name.split(" ")[1].rstrip(":")
            node_link = BASE_URL + "/" + top_level_title + link_container['href'].replace("./", "/")
            print(node_link)
            node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            print(node_name)
            if ("Chapter 97: LIMITED LINES SELF-STORAGE INSURANCE (REPEALED)" in node_name):
                continue
            # Check for reserved
            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved"
                    break
            
            print(node_name)
            try:
                insert_node(node_data)
                print(node_id)  
            except:
                print("** Skipping:",node_id)
                continue

            # Find the next round of structure nodes
            if node_type != "reserved":
                response = urllib.request.urlopen(node_link)
                data = response.read()      # a `bytes` object
                text = data.decode('utf-8') # a `str`; 
                soup = BeautifulSoup(text, features="html.parser")
                print(node_link)

                title_container = soup.find("div", class_="chapter_toclist col-sm-10")
                # Checking for section case
                
                title_tags = title_container.find("div", class_="ch_heading")
                next_div_elements = title_tags.find_next_siblings("div")
                if len(next_div_elements) == 1:
                    next_div_elements = next_div_elements[0].find_all(recursive=False)

                scrape_level(next_div_elements, node_link, top_level_title, node_id)


  

def scrape_section(url, top_level_title, node_parent, node_name):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text, features="html.parser")

    section_container = soup.find("div", class_="col-sm-12 MRSSection status_current")
    node_name = node_name
    print(node_name)
    print(url)

    node_number = node_name.split(" ")[1].rstrip(".").replace("§","")
    node_level_classifier = "SECTION"
   
    node_link = url
    node_id = f"{node_parent}{node_level_classifier}={node_number}"

    node_text = []

    if section_container is None:
        section_text = soup.find_all("div", class_="MRSSection_toclist ")
    else:
        section_text = section_container.find_all("div")
    
        
                
    node_addendum = None
    node_type = "content"

    for text in section_text:
        if 'qhistory' in text.get('class', []):
            node_addendum_get = text.get_text().strip()
            temp2 = node_addendum_get.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').strip()
            temp = re.sub(r'\s+', ' ', temp2)
            node_addendum = temp
        else:
            span = text.find("span")
            if span is not None:
                span.decompose() 
            node_text_add = text.get_text().strip()
            temp2 = node_text_add.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').strip()
            temp = re.sub(r'\s+', ' ', temp2)
            node_text.append(temp)



    node_citation = f"{top_level_title} MRS § {node_number}"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    
    base_node_id = node_id
    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            break
    for i in range(2, 10):
            try:
                insert_node(node_data)
                print(node_id)
                
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{i}"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            continue
        
    


    ### FOR ADDING A CONTENT NODE, allowing duplicates
    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # base_node_id = node_id
    
    # for i in range(2, 10):
    #     try:
    #         insert_node(node_data)
    #         #print("Inserted!")
    #         break
    #     except Exception as e:   
    #         print(e)
    #         node_id = base_node_id + f"-v{i}/"
    #         node_type = "content_duplicate"
    #         node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    #     continue
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "me/",
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
        "me/statutes/",
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
        "me/",
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