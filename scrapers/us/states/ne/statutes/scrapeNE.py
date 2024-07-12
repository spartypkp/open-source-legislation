import psycopg2
import os
import urllib.request
import json
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

 = "will2"
TABLE_NAME = "ne_node"
BASE_URL = "https://nebraskalegislature.gov"
TOC_URL = "https://nebraskalegislature.gov/laws/browse-statutes.php"


def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < 80:
                continue
            
            
            scrape_per_title(line.strip())
            

def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    og_parent = "ne/statutes/"

    title_container = soup.find(class_="card-header leg-header")
    title_name = title_container.get_text().strip()
    title_name = title_name.replace("Revised Statutes ", "")
    top_level_title = title_name.split(" ")[1]
    node_level_classifier = "CHAPTER"
    node_type = "structure"
    node_link = url
    title_node_id = f"{og_parent}CHAPTER={top_level_title}/"
    print(title_node_id)
    node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, title_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node(node_data)

    section_container = soup.find(class_="card-body").table
    for i, section in enumerate(section_container.find_all("tr")):
        td = section.td
        all_spans = td.find_all(recursive=False)
        node_link_container = all_spans[0]
        link = node_link_container.find("a")
        node_link = BASE_URL + link['href']
        node_number = link.get_text().strip().replace("View Statute ", "")
        node_number = node_number.split("-")[1]

        node_name_container = all_spans[1]
        node_name = node_name_container.get_text().strip()
        node_id = f"{title_node_id}SECTION={node_number}"
        node_type = "content"

        if "repealed" in node_name.lower() or "unconstitutional." in node_name.lower() or "transferred to " in node_name.lower():
            node_type = "reserved"

        
        if node_type != "reserved":
            response2 = urllib.request.urlopen(node_link)
            data2 = response2.read()      # a `bytes` object
            text2 = data2.decode('utf-8') # a `str`; 
            section_soup = BeautifulSoup(text2, features="html.parser")

            node_text = []
            node_citation = f"Neb. Rev. Stat. § {top_level_title}-{node_number}"
            node_addendum = ""
            node_references = {}
            node_level_classifier = "SECTION"

            node_tags = {}

            text_container = section_soup.find(class_="statute")
            internal = []
            for i, p in enumerate(text_container.find_all(["p","div"], recursive=False)):
                
                txt = p.get_text().strip()
                if 'class' in p.attrs:
                    if p['class'][0] == "text-justify":
                        node_text.append(txt)
                        for a in p.find_all("a"):
                            temp = {"text": a.get_text(), "link": BASE_URL+a['href']}
                            internal.append(temp)
                    else:
                        node_tags[p['class'][0]] = txt
                        for a in p.find_all("a"):
                            temp = {"text": a.get_text(), "link": BASE_URL+a['href']}
                            internal.append(temp)
                else:
                    if p.find(class_="fa-ul") is not None:
                        node_addendum = txt
                        addendum_references = []
                        for a in p.find_all("a"):
                            temp = {"text": a.get_text(), "link": BASE_URL+a['href']}
                            addendum_references.append(temp)
                        if len(addendum_references) > 0:
                            node_tags["addendum_references"] = addendum_references
            if len(internal) > 0:
                node_tags["internal_references"] = internal
            if node_tags:
                node_tags = json.dumps(node_tags)
            else:
                node_tags = None
            if node_references:
                node_references = json.dumps(node_references)
            else:
                node_references = None
        else:
            node_text = None
            node_citation = None
            node_addendum = None
            node_references = None
            node_tags = None

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, title_node_id, None, None, node_references, None, node_tags)
        print(node_id)
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
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, title_node_id, None, None, node_references, None, node_tags)
            continue
        





                        
           




def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ne/",
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
        "ne/statutes/",
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
        "ne/",
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