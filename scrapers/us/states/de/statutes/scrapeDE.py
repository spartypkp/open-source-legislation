from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import re
import sys
import psycopg2
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from urllib.error import URLError
from node import Node
import json


BASE_URL = "https://delcode.delaware.gov"
TABLE_NAME = "de_node"
 = "madeline"
RESERVED_KEYWORDS = ["Repealed", "Expired", "Reserved"]
SKIP_TITLE = 0

# MOST OF THE TIME: ["TITLE", "PART", "CHAPTER", "SECTION"]
# Going to chapter will bring you to the sections page (sometimes part)



def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file, start=1):  # Start enumeration from 1
            # if i < 8:
            #     continue 
            if i < SKIP_TITLE:
                continue
  
            url = line
            # print(url)
            # exit(1)
            if ("title" in url):
                top_level_title = url.split("title")[-1].strip()
                top_level_title = top_level_title.rsplit('/', 1)[0]

                scrape_per_title(url, top_level_title, "de/statutes/")
            elif ("constitution" in url):
                continue
                # top_level_title = "CONSTITUTION"
                # scrape_constitution(url, top_level_title, "de/statutes/")
            else:
                continue
            

def scrape_per_title(url, top_level_title, node_parent):
    
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")


    title_container = soup.find("div", id="content")
    title_tags = title_container.find("div", class_="row")
    title_name_tag = title_tags.find("h2")
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
    
    div_elements = title_tags.find_next_siblings("div")
    # If div is length 1, get all the children
    if len(div_elements) == 1:
        div_elements = div_elements[0].find_all(recursive=False)

    scrape_level(div_elements, url, top_level_title, node_id)
    

# Handles any generic structure node, routes sections to scrape_sections
def scrape_level(div_elements, url, top_level_title, node_parent):
    
    # Iterate over the container of the structure nodes
    for i, div in enumerate(div_elements):
        #print(div.prettify())
        
        # Handle the case of the "subtitle header"
        all_headers = div.find_all("h3", recursive=False)

        # Guranteed structure node
        if len(all_headers) > 0:
            # Extract structure node information
            # "Part I" + " " + "Administrative Agencies"
            node_name = all_headers[0].get_text().strip() + " " + all_headers[1].get_text().strip()
            node_type = "structure"
            node_level_classifier = node_name.split(" ")[0].upper()
            node_number = node_name.split(" ")[1]
            if node_number[-1] == ".":
                node_number = node_number[:-1]
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
        
        # A link is found for this div
        elif div.find("a", recursive=False) is not None:
            link_container = div.find("a", recursive=False)
            node_name = link_container.get_text().strip()
            
            
            node_type = "structure"
            node_level_classifier = node_name.split(" ")[0].upper()
            node_number = node_name.split(" ")[1]
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            node_link = BASE_URL + link_container['href'].replace("../", "/")
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

            # Find the next round of structure nodes
            if node_type != "reserved":
                response = urllib.request.urlopen(node_link)
                data = response.read()      # a `bytes` object
                text = data.decode('utf-8') # a `str`; 
                soup = BeautifulSoup(text, features="html.parser")

                title_container = soup.find("div", id="content")
                # Checking for section case
                if title_container.find(id="CodeBody") is not None:
                    # BAD CASE!
                    if title_container.find(class_="Section") is None:
                        
                        continue
                    next_div_elements = title_container.find_all(class_="Section")
                    scrape_sections(next_div_elements, node_link, top_level_title, node_id)
                else:
                    title_tags = title_container.find("div", class_="row")
                    next_div_elements = title_tags.find_next_siblings("div")
                    if len(next_div_elements) == 1:
                        next_div_elements = next_div_elements[0].find_all(recursive=False)

                    scrape_level(next_div_elements, node_link, top_level_title, node_id)
                

def scrape_sections(div_elements, node_link, top_level_title, node_parent):
    # Scrape a section regularly
    
    
    for i, div in enumerate(div_elements):
        
        section_header = div.find(class_="SectionHead")
        temp = section_header.get_text().strip()
        node_name = temp.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').replace('§§', '').strip().rstrip(".")
        node_name = re.sub(r'\s+', ' ', node_name)
        node_number = section_header['id']
        node_number = node_number.replace(",", "-").rstrip(".")
            
        node_type = "content"
        node_level_classifier = "SECTION"
        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        

        for word in RESERVED_KEYWORDS:
            if word in node_name:
                node_type = "reserved"
                node_name = node_name.replace(" ", "-")
                node_id = f"{node_parent}{node_level_classifier}={node_number}{node_name}"
                break
        
        node_text = []
        node_citation = f"{top_level_title} Del. C. § {node_number}"

        # Finding addendum
        node_addendum = ""
        node_tags = {}
        addendum_references = []

        if node_type != "reserved":
            for element in div.find_all(recursive=False):
                # Skip the sectionHead
                if 'class' in element.attrs and element['class'][0] == "SectionHead":
                    continue
                
                
                # I want to remove all &nbsp; and &ensp; from the elements text
                temp = element.get_text().strip()
                text = temp.replace('\xc2\xa0', '').replace('\u2002', '').replace('\n', '').replace('\r            ', '').strip()
                text = re.sub(r'\s+', ' ', text)
                
                
                if element.name == "p":
                    node_text.append(text)
                    continue
                

                # Assume any left over text without a <p> tag is the addendum
                node_addendum += text + " "
                
                if element.name == "a":
                    addendum_references.append({"Citation": text, "link": element['href']})
                



            
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
    



        

        
            
    




# def scrape_constitution(url, top_level_title, node_parent):
#     response = urllib.request.urlopen(url)
#     data = response.read()      # a `bytes` object
#     text = data.decode('utf-8') # a `str`; 
#     soup = BeautifulSoup(text)

#     soup = soup.find("div", id="content")
#     title_tag = soup.find("h2")
#     node_name = title_tag.get_text().strip()
#     node_number = top_level_title
#     node_type = "structure"
#     node_level_classifier = "TITLE"
#     node_id = f"{node_parent}TITLE={node_number}/"
#     node_link = url
#     title_node_parent = node_id

#     node_text = None
#     node_citation = None
#     node_addendum = None
#     node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
#     insert_node(node_data)

#     chapter_links = soup.find_all("p")


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "de/",
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
        "de/statutes/",
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
        "de/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)





@retry(
    retry=retry_if_exception_type(URLError),       # Retry on URLError
    wait=wait_exponential(multiplier=1, max=60),   # Exponential backoff with a max wait of 60 seconds
    stop=stop_after_attempt(5)                     # Stop after 5 attempts
)
def make_request(url):
    try:
        # Attempt to open the URL
        response = urllib.request.urlopen(url)
        return response

    except urllib.error.HTTPError as e:
        # Check if the error is a 404 Not Found
        if e.code == 404:
            print(f"URL not found, skipped: {url}")
            return None


if __name__ == "__main__":
     main() 