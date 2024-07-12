import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
import json

 = "will2"
TABLE_NAME = "mn_node"
BASE_URL = "https://www.revisor.mn.gov"
TOC_URL = "https://www.revisor.mn.gov/statutes/"

def main():
    insert_jurisdiction_and_corpus_node()
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="toc_table").tbody
    all_rows = soup.find_all("tr")
    og_parent = "mn/statutes/"
    
    for i, row in enumerate(all_rows):
        if i < 25:
            continue
        
        
        all_tds = row.find_all("td")
        link_container = all_tds[0]
        link = link_container.find("a")
        top_level_title = link.get_text().strip().replace(" ", "")
        node_link = "https:" + link['href']
        part_container = all_tds[1]
        part_name = part_container.get_text().strip()
        
        node_type = "structure"
        node_level_classifier = "PART"
        part_node_id = f"{og_parent}PART={top_level_title}/"
        
        title_node_data = (part_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(title_node_data)
        scrape_per_part(node_link, top_level_title, part_node_id)
        
            
            
    
def scrape_per_part(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    chapters_table = soup.find(id="chapters_table")
    for i, chapter in enumerate(chapters_table.tbody.find_all("tr")):
        all_tds = chapter.find_all("td")
        link_container = all_tds[0]
        link = link_container.find("a")
        node_number = link.get_text().strip()
        
        node_link = "https:" + link['href']

        chap_container = all_tds[1]
        node_name = chap_container.get_text().strip()
        node_level_classifier = "CHAPTER"
        node_type = "structure"
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        scrape_sections(node_link, top_level_title, node_id)

def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    last_category = None
    container = soup.find(id="chapter_analysis").table
    all_sections = container.tbody.find_all("tr")
    for i, section in enumerate(all_sections):
        if 'class' in section.attrs:
            last_category = section.get_text().strip()
            continue
        all_tds = section.find_all("td")
        link_container = all_tds[0]
        link = link_container.find("a")
        node_number = link.get_text().strip()
        node_link = BASE_URL + link['href']

        sec_container = all_tds[1]
        node_name = sec_container.get_text().strip()
        node_level_classifier = "SECTION"
        node_type = "content"
        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        print(node_id)
        
        
        node_text = []
        node_addendum = ""
        node_citation = f"Minnesota Statutes, section {node_number}"
        node_references = None
        node_tags = {}

        if "repealed" in node_name.lower() or "renumbered" in node_name.lower() or "[" in node_name.lower():
            node_type = "reserved"
        else:

            response2 = urllib.request.urlopen(node_link)
            data2 = response2.read()      # a `bytes` object
            text2 = data2.decode('utf-8') # a `str`; 
            section_soup = BeautifulSoup(text2, features="html.parser")

            node_addendum_container = section_soup.find(class_="history")
            if node_addendum_container is not None:
                node_addendum = node_addendum_container.get_text().strip()
                addendum_references = []
                for a in node_addendum_container.find_all("a"):
                    temp = {"text": a.get_text(), "link": BASE_URL+a['href']}
                    addendum_references.append(temp)
                if len(addendum_references) > 0:
                    node_tags["addendum_references"] = addendum_references
            else:
                node_addendum = None
            
            
            
            
            text_container = section_soup.find(class_="section")
            for p in text_container.find_all():
                txt = p.get_text().strip()
                node_text.append(txt)

        if last_category is not None:
            node_tags["category"] = last_category
        if node_tags == {}:
            node_tags = None
        else:
            node_tags = json.dumps(node_tags)

        #print("Trying to insert here!")
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        base_node_id = node_id
        
        for i in range(2, 10):
            try:
                insert_node(node_data)
                #print("Inserted!")
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{i}/"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue





def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "mn/",
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
        "mn/statutes/",
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
        "mn/",
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