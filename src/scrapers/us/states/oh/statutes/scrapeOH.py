import psycopg2
import os
from bs4 import BeautifulSoup
import urllib.request
import sys
import json
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "will2"
TABLE_NAME = "oh_node"
BASE_URL = "https://codes.ohio.gov/ohio-revised-code/"

def main():
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for line in read_file:
            print(line)
            scrape_per_title(line.strip())
            

def scrape_per_title(title_url):
    node_parent = "oh/statutes/"
    response = urllib.request.urlopen(title_url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    node_name = title_url.split("/")[-1].replace("-","_")
    
    if ("title" not in node_name):
        node_number = 0
    else:
        node_number = node_name.split("_")[1]
    node_level_classifier = "title"
    node_type = "structure"
    top_level_title = node_number
    title_node_id = f"oh/statutes/{node_level_classifier.upper()}={node_number}/"
    title_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, title_url, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(title_data)
    node_parent = title_node_id

    # Get all chapters
    chapter_container = soup.find(class_="data-grid laws-table")
    
    all_chapters = chapter_container.find_all(class_="name-cell")
    for chap in all_chapters:
        a_tag = chap.find("a")
        chapter_url = BASE_URL + a_tag["href"]
        node_name = a_tag.get_text()
        chapter_info = node_name.split("|")[0]
        node_number = chapter_info.split(" ")[1]
        node_level_classifier = chapter_info.split(" ")[0]
        node_type = "structure"
        node_id = f"{node_parent}{node_level_classifier.upper()}={node_number}/"
        node_text, node_citation, node_addendum, node_references, node_tags = None, None, None, None, None
        node_link = chapter_url
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        for i in range(2, 10):
            try:
                insert_node(node_data)
                break
            except:
                node_id = node_id[:-1] + f"-v{i}/"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue
        scrape_all_sections(chapter_url, top_level_title, node_id)


def scrape_all_sections(chapter_url, top_level_title, node_parent):
    response = urllib.request.urlopen(chapter_url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    sections_container = soup.find(class_="data-grid laws-table")
    all_sections = sections_container.find_all(class_="name-cell")
    for section in all_sections:
        div = section.find("div", recursive=False)
        link_container = div.find(class_="content-head-text").find("a")
        node_link = BASE_URL + link_container["href"]
        node_name = link_container.get_text()
        chapter_info = node_name.split("|")[0]
        node_number = chapter_info.split(" ")[1]
        node_level_classifier = "section"
        node_type = "content"
        node_id = f"{node_parent}{node_level_classifier.upper()}={node_number}"
        print(node_id)
        node_text = []
        node_citation = f"Ohio Rev. Code § {node_number}"
        node_addendum = ""
        node_references = {}
        node_tags = None
        
        addendum_info_container = section.find_all(class_="laws-section-info-module")
        for info_module in addendum_info_container:
            node_addendum += info_module.get_text()
        
        node_text_container = section.find(class_="laws-body")
        internal_references = []
        external_references = []
        for i, p in enumerate(node_text_container.find_all(recursive=True)):
            
            if (p.name == "a"):
                #print(p)
                internal = {"href": p['href'], "text": p.get_text()}
                citation = f"Ohio Rev. Code § {p.get_text()}"
                internal['citation'] = citation
                internal_references.append(internal)

            node_text.append(p.get_text())
        
        
        #print(internal_references)
        if internal_references:
            node_references['internal'] = internal_references
        if external_references:
            node_references['external'] = external_references
        if node_references:
            node_references = json.dumps(node_references)
        else:
            node_references = None
                

        
        #print(node_text)
        

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        for i in range(2, 10):
            try:
                insert_node(node_data)
                break
            except:
                node_id = node_id[:-1] + f"-v{i}"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue
    




    





def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "oh/",
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
        "oh/statutes/",
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
        "mhl/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)






if __name__ == "__main__":
    main()