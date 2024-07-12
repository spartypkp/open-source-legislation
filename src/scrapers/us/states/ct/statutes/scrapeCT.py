import psycopg2
import os
import json
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "will"
TABLE_NAME = "ct_node"
BASE_URL = "https://www.cga.ct.gov"
TOC_URL = "https://www.cga.ct.gov/current/pub/titles.htm"
SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n

def main():
    insert_jurisdiction_and_corpus_node()
    scrape()

def scrape():
     
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="titles.htm")
    all_links = soup.find_all(class_="left_38pct")

    og_parent = "ct/statutes/"
    for title in all_links:
        link = title.find("a")
        name_container = title.next_sibling.next_sibling
        try:
            node_name_start = link.get_text().strip()
            node_link = "https://www.cga.ct.gov/current/pub/" + link['href'] + "\n"
            node_name_end = name_container.find("a").get_text()
        except:
            node_name_start = title.find(class_="toc_ttl_desig").get_text().strip()
            node_name_end = name_container.find(class_="toc_ttl_name").get_text().strip()
            node_type = "reserved"
            node_link = TOC_URL

        top_level_title = node_name_start.split(" ")[1]
        node_descendants = title.find(class_="toc_rng_chaps").get_text().strip()
        
        
        node_level_classifier = "TITLE"
        node_type = "structure"
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
        print(node_id)
        node_name = f"{node_name_start} {node_name_end}"
        node_tags = json.dumps({"descendants": node_descendants})


        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, node_tags)
        insert_node_ignore_duplicate(node_data)
        if node_type != "reserved":
            scrape_chapters(node_link, top_level_title, node_id)

            
    

def scrape_chapters(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    #### Extract structure_node information from the url
    for i, chapter in enumerate(soup.find_all(class_="left_40pct")):
        link = chapter.find("a")
        try:
            node_name_start = link.get_text().strip()
        except:
            return
        node_number = node_name_start.split(" ")[1]
        node_link = "https://www.cga.ct.gov/current/pub/" + link['href'] + "\n"
        node_descendants = chapter.find(class_="toc_rng_secs").get_text().strip()
        name_container = chapter.next_sibling.next_sibling
        node_name_end = name_container.find("a").get_text()
        node_level_classifier = "CHAPTER"
        node_type = "structure"
        node_name = f"{node_name_start} {node_name_end}"
        node_tags = json.dumps({"descendants": node_descendants})
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
       
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
        ## INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        scrape_sections(node_link, top_level_title, node_id)
        


    # This is only for the last scrape_level
    # if node_type != "reserved":
    #     scrape_section(url, top_level_title, node_parent)

def scrape_sections(url, top_level_title, node_parent):
    
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser").find("div")
    while True:
        br_tag = soup.find("br", recursive=False)
        if br_tag is None:
            break
        br_tag.decompose()
        print("Decomposed 1 tag!")


    for i, section in enumerate(soup.find_all(class_="toc_catchln")):
        link = section.find("a")

        

        node_sec_id = link['href'].replace("#","")
        node_number = node_sec_id.split("-")[-1]
        node_link = url + link['href']
       
        node_name = link.get_text().strip()
        node_level_classifier = "SECTION"
        node_type = "content"
        if section.find("b") is not None:
            node_type = "reserved"
        node_id = f"{node_parent}{node_level_classifier}={node_number}"

        if node_type != "reserved":
            node_text = []
            node_addendum = ""
            node_citation = f"Conn. Gen. Stat. § {top_level_title}-{node_number}"
            node_references = {}
            node_tags = {}
            annotations = []
            internal = []
            external = []
            counter = 0
            iterator = soup.find(id=f"{node_sec_id}").parent
            while iterator:
                
                if iterator.name == "table" and 'class' in iterator.attrs and iterator['class'][0] == "nav_tbl":
                    break

                txt = iterator.get_text().strip()
                #print(txt)
                if iterator.name != "p":
                    node_text.append(txt)
                    
                    iterator = iterator.next_sibling.next_sibling
                    continue
                
                for sec_link in iterator.find_all("a"):
                    cit = sec_link.get_text().strip()
                    lnk = "https://www.cga.ct.gov/current/pub/" + sec_link['href']
                    if "#" in lnk:
                        internal.append({cit: lnk})
                    else:
                        external.append({cit: lnk})


                    
                
                # Regular text
                if 'class' not in iterator.attrs:
                    node_text.append(txt)
                else:
                    if iterator['class'][0] == "source-first":
                        node_addendum = txt
                    elif iterator['class'][0] == "history-first":
                        node_tags['history'] = txt
                    else:
                        
                        annotations.append(txt)
                iterator = iterator.next_sibling.next_sibling

            if len(internal) > 0:
                node_references["internal"] = internal
            if len(external) > 0:
                node_references["external"] = external
            if node_references != {}:
                node_references = json.dumps(node_references)
            else:
                node_references = None
            
            if len(annotations) > 0:
                node_tags["annotations"] = annotations
            
            if node_tags != {}:
                node_tags = json.dumps(node_tags)
            else:
                node_tags = None
        else:
            node_text = None
            node_addendum = None
            node_citation = None
            node_references = None
            node_tags = None

        ### FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        base_node_id = node_id
        
        for i in range(2, 10):
            try:
                insert_node(node_data)
                print(node_id)
                #print("Inserted!")
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{i}/"
                
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue
            


    
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ct/",
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
        "ct/statutes/",
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
        "ct/",
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