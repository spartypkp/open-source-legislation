import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
import json
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "will"
TABLE_NAME = "mo_node"
BASE_URL = "https://revisor.mo.gov"
TOC_URL = "https://revisor.mo.gov/main/Home.aspx"

def main():
    scrape()

def scrape():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    container = soup.find(id="BOTTOM").find_previous_sibling()
    all_titles = container.find_all(recursive=False)[1].find_all("details")
    
    
    og_parent = "mo/statutes/"
    for title_raw in all_titles:
        title = title_raw.find("summary")
        #print(title)
        temp = title.find_all(recursive=False)[1]
        
        
        title_node_name = temp.get_text().strip().replace("\u2003", " ")
        
        top_level_title = title_node_name.split(" ")[0]

        title_node_id = f"{og_parent}TITLE={top_level_title}/"
        title_node_level_classifier = "TITLE"
        title_node_link = TOC_URL
        title_node_type = "structure"

        
       
        node_data = (title_node_id, top_level_title, title_node_type, title_node_level_classifier, None, None, None, title_node_link, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        
        # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, article_node_id, None, None, node_references, None, node_tags)

        all_chapters = title_raw.find_all("a")
        for chapter in all_chapters:
            node_name = chapter.get_text().strip().replace("\u2003", " ").strip()
            node_number = node_name.split(" ")[0]
            node_level_classifier="CHAPTER"
            node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
            node_link = BASE_URL + chapter['href']
            node_type = "structure"
            
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
            try:
                insert_node(node_data)
            except:
                print("** Skipping: ", node_id)
                continue
                
            print(node_id)
            node_parent = node_id
            scrape_sections(top_level_title, node_parent, node_link)
    
def scrape_sections(top_level_title, node_parent, url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    find_it = container = soup.find(id="BOTTOM").find_previous_sibling()
    container = find_it.find("table")
    
    last_act_category = None
    for i, row in enumerate(container.find_all("tr")):
        if row.find("a") is None:
            last_act_category = row.get_text().strip()
            continue
        all_tds = row.find_all("td")
        link_container = all_tds[0]
        link = link_container.find("a")
        node_name_start = link.get_text().strip()
        node_number = node_name_start
        
        node_link = BASE_URL + link['href']

        name_container = all_tds[1]
        node_name_end = name_container.get_text().strip()
        node_name = node_name_start + " " + node_name_end
        node_level_classifier = "SECTION"
        node_type = "content"
        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        print(node_id)

        response2 = urllib.request.urlopen(node_link)
        data2 = response2.read()      # a `bytes` object
        text2 = data2.decode('utf-8') # a `str`; 
        section_soup = BeautifulSoup(text2, features="html.parser")

        div = section_soup.find(id="BOTTOM").find_previous_sibling()
        div2 = div.find("div")
        
        text_container = div2.find_all(recursive=False)[1]

        node_text = []
        node_addendum = ""
        node_citation = f"Mo. Rev. Stat. § {node_number}"
        node_references = {}
        node_tags = None


        all_text = text_container.find_all(recursive=False)
        for i, tag in enumerate(all_text):
            txt = tag.get_text().strip()
            if i == len(all_text)-1:
                node_addendum = txt
                continue
            all_links = tag.find_all("a")
            for link in all_links:
                link_text = link.get_text().strip()
                link_url = BASE_URL + link['href']
                node_references[link_text] = link_url
            

            node_text.append(txt)
        if node_references == {}:
            node_references = None
        else:
            node_references = json.dumps(node_references)

        if last_act_category is not None:
            node_tags = {"Act Category": last_act_category}
            node_tags = json.dumps(node_tags)
        base_node_id = node_id
        
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        for i in range(2, 10):
            try:
                insert_node(node_data)
                break
            except:
                
                node_id = base_node_id + f"-v{i}/"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        









            

        



def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "mo/",
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
        "mo/statutes/",
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
        "mo/",
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