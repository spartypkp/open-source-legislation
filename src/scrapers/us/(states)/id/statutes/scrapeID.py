import psycopg2
import os
import sys
import urllib.request
from bs4 import BeautifulSoup
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "will"
TABLE_NAME = "id_node"
BASE_URL= "https://legislature.idaho.gov"



# TITLE 41
def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for line in read_file:
            url = line.strip()
            top_level_title = int(url.split("/")[-1].replace("Title",""))
            if top_level_title < 72:
                continue
            print(url)
            print(top_level_title)
            scrape_per_title(url, top_level_title)
    



def scrape_per_title(url, top_level_title):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    title_container = soup.find(class_="lso-toc")
    title_name = title_container.get_text()
    title_node = f"id/statutes/TITLE={top_level_title}/"
    #print(title_node)
    node_data = (title_node, top_level_title, "structure", "TITLE", None, None, None, url, None, title_name, None, None, None, None, None, "id/statutes/", None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    scrape_structures(url, top_level_title, title_node)
    

def scrape_structures(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    #print(url)
    title_container = soup.find(class_="lso-toc")
    table_container = title_container.parent
    table = table_container.find("table")
    rows = table.find_all("tr")
    for row in rows:
        all_tds = row.find_all("td")
        link_container = all_tds[0]
        try:
            link = link_container.find("a")
            node_link  = BASE_URL + link['href']
            node_type = "structure"
        except:
            node_link = url
            node_type = "reserved"

       
        if  "SECT" in node_link and node_type !=  "reserved":
            node_name = link.get_text().strip() + " " + all_tds[2].get_text().strip()
            #print(node_name)
            node_number = node_name.split(" ")[0]
            node_number = node_number.split("-")[-1]
            #print(node_number)
            node_level_classifier = "SECTION"
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            node_type = "content"
            scrape_section(node_link, top_level_title, node_parent, node_name, node_level_classifier,node_id, node_number)
            #print("CONTINUED!")
            continue
        
        
        try:
            node_name_start  = link_container.get_text()
            #print(node_name_start)
            node_level_classifier = node_name_start.split(" ")[0].upper()
            node_number  = node_name_start.split(" ")[1]
            node_number = node_number.replace(".","")
            if "[" in node_name_start and "]" in node_name_start:
                # Set the node number to the number in the brackets
                node_number = node_name_start.split("[")[1].split("]")[0]

        except:
            continue

        name_container = all_tds[2]
        node_name_end  = name_container.get_text()
        node_name = node_name_start + " " + node_name_end
        if "REDESIGNATED" in node_name:
            node_type = "reserved"

        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        print(node_id)
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node(node_data)
        if node_type != "reserved":
            scrape_structures(node_link, top_level_title, node_id)

def scrape_section(url, top_level_title, node_parent, node_name, node_level_classifier,node_id, node_number):
    #print(url)
    #print("HERE!")
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    
    container = soup.find(class_="pgbrk")

    node_text = []
    node_addendum = ""
    node_citation = f"I.C. {top_level_title} § {node_number}"
    node_tags = None
    node_references = None
    found_addendum = False
    node_link = url
    for i, div in enumerate(container.find_all("div")):
        if i < 4:
            continue
        
        txt = div.get_text().strip()
        if found_addendum or "History:" in txt:
            found_addendum = True
            node_addendum += txt
        else:
            node_text.append(txt)
    base_node_id = node_id[:-1]
    print(f"  - {node_id}")
    node_data = (node_id, top_level_title, "SECTION", node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    for i in range(2, 10):
        try:
            insert_node(node_data)
            #print(f"inserting!\n{node_data}")
            break
        except:
            #print("Exception!")
            node_id = base_node_id + f"-v{i}/"
            node_type = "content_duplicate"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        continue
                    
                    
                        


        

    

def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "id/",
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
        "id/statutes/",
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
        "id/",
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