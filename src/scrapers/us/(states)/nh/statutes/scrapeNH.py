import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from bs4.element import Tag

 = "will2"
TABLE_NAME = "nh_node"
BASE_URL = "https://www.gencourt.state.nh.us/rsa/html/"
TOC_URL = "https://www.gencourt.state.nh.us/rsa/html/nhtoc.htm"
SKIP_TITLE = 3 # If you want to skip the first n titles, set this to n
RESERVED_KEYWORDS = ["Repealed"]

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_per_title(url)
    

def scrape_per_title(url):
    # response = urllib.request.urlopen(url)
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    title_container = soup.find("body")
    title_center_tags = title_container.find_all("center")
    title_name = title_center_tags[2].get_text()
    if title_name == "":
        return
        

    title_number = title_name.split()[0].replace(":","")
    #print(title_name)
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"nh/statutes/TITLE={title_number}/"
    node_link = url
    title_node_data = (node_id, title_number, node_type, node_level_classifier, None, None, None, node_link, None, title_name, None, None, None, None, None, "nh/statutes/", None, None, None, None, None)
    insert_node_ignore_duplicate(title_node_data)
    node_parent = node_id
    print(node_id)
    top_level_title = title_number

    chapter_links = title_container.find_all("a")

    for chapter in chapter_links:
        BASE_URL2 = "https://www.gencourt.state.nh.us/rsa/html/NHTOC/"
        url = BASE_URL2 + chapter['href']
        scrape_per_chapter(url, top_level_title, node_parent)
    
def scrape_per_chapter(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8')
    soup = BeautifulSoup(text, features="html.parser")

    chapter_container = soup.find("body")
    chapter_center_tags = chapter_container.find_all("center")
    chapter_name = chapter_center_tags[2].get_text()
    chapter_number_get = chapter_name.split(" ")[1]
    chapter_number = chapter_number_get.replace(":","")
    
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_id = f"{node_parent}CHAPTER={chapter_number}/"
    node_link = url
    chapter_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    try:
        insert_node(chapter_node_data)
        print(node_id)
    except:
        print("** Skipping:",node_id)
        return
    node_parent = node_id
    top_level_title = top_level_title

    section_container = chapter_container.find("ul")
    section_links = section_container.find_all("a")

    for section in section_links:
        href = section['href']
        processed_href = href.replace("../", "")
        url = BASE_URL + processed_href
        scrape_per_section(url, top_level_title, node_parent)


def scrape_per_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    


    node_type = "content"
    node_level_classifier = "SECTION"
    node_text = []

    section_container = soup.find("body")
    
    
    

    section_name_container = section_container.find("b")
    node_name = section_name_container.get_text().strip()
    if node_name[-1] == "-":
        node_name = node_name[:-1]
    node_citation_raw = node_name.split(" ")[0]
    node_number = node_citation_raw.split(":")[-1]

   
    node_addendum = section_container.find("sourcenote").get_text().strip()
    node_citation = f"NH Rev Stat § {node_citation_raw}"

    node_id = f"{node_parent}SECTION={node_number}"
    node_link = url

    for word in RESERVED_KEYWORDS:
        if word in node_name:
            node_type = "reserved"
            break
    if node_type != "reserved":
        section_text_container = section_container.find("codesect")
        node_text = []
        for element in section_text_container:
            if isinstance(element, Tag):
                continue
            txt = element.strip()
            if txt != "":
                node_text.append(txt)
    else:
        node_text = None

    node_references = None
    node_tags = None

     ### FOR ADDING A CONTENT NODE, allowing duplicates
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    base_node_id = node_id
    
    for j in range(2, 10):
        try:
            insert_node(node_data)
            print(node_id)
            break
        except Exception as e:   
            print(e)
            node_id = base_node_id + f"-v{j}"
            node_type = "content_duplicate"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        continue
    
  

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "nh/",
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
        "nh/statutes/",
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
        "nh/",
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