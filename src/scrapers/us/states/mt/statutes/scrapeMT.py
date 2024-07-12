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

 = "will2"
TABLE_NAME = "mt_node"
BASE_URL = "https://leg.mt.gov"
TOC_URL = "https://leg.mt.gov/bills/mca/index.html"

def main():
    insert_jurisdiction_and_corpus_node()
    scrape_titles()

def scrape_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    og_parent = "mt/statutes/"
    container = soup.find(class_="mca-content mca-toc")
    all_links = container.find_all("a")
    for title in all_links:
        
        node_link = "https://leg.mt.gov/bills/mca" + title.attrs['href'][1:]
        top_level_title = title['data-titlenumber']
        node_name = title.get_text().strip().replace('\xa0', ' ')
        node_type = "structure"
        node_level_classifier = "TITLE"
        title_node_id = f"{og_parent}TITLE={top_level_title}/"
        print(title_node_id)
        node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        scrape_chapters(node_link, top_level_title, title_node_id)

def scrape_chapters(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    all_chapter_container = soup.find(class_="chapter-toc-content")
    for i, chapter in enumerate(all_chapter_container.find_all(class_="line")):
        link_container = chapter.find("a")
        if link_container is None:
            node_name = chapter.get_text().strip().replace('\xa0', ' ')
            node_number = node_name.split(" ")[1]
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            node_type = "reserved"
            node_link = url
        else:
            node_name = link_container.get_text().strip().replace('\xa0', ' ')
            try:
                node_number = node_name.split(" ")[1]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]
            except:
                node_number = node_name.replace(" ", "_")
            new_url = url.split("/")
            new_url.pop()
            new_url = "/".join(new_url)
            node_link = new_url + link_container.attrs['href'][1:]
            node_type = "structure"
        node_level_classifier = "CHAPTER"
        chapter_node_id = f"{node_parent}CHAPTER={node_number}/"
        print(chapter_node_id)
        node_data = (chapter_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        
        insert_node(node_data)
        if node_type != "reserved":
            scrape_parts(node_link, top_level_title, chapter_node_id)

def scrape_parts(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    all_part_container = soup.find(class_="part-toc-content")

    for i, part in enumerate(all_part_container.find_all(class_="heading")):
        link_container = part.find("a")
        if link_container is None:
            node_name = part.get_text().strip().replace('\xa0', ' ')
            
            node_number = node_name.split(" ")[1]
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            node_type = "reserved"
            node_link = url
        else:
            node_name = link_container.get_text().strip().replace('\xa0', ' ')
            #print(node_name)
            
            try:
                node_number = node_name.split(" ")[1]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]
            except:
                node_number = node_name.replace(" ", "_")
            
            new_url = url.split("/")
            new_url.pop()
            new_url = "/".join(new_url)
            node_link = new_url + link_container.attrs['href'][1:]
            node_type = "structure"
        node_level_classifier = "PART"
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        print(node_id)
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node(node_data)
        if node_type != "reserved":
            scrape_sections(node_link, top_level_title, node_id)

def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    all_section_container = soup.find(class_="section-toc-content")

    for i, section in enumerate(all_section_container.find_all(class_="line")):
        #print(section)
        node_citation = None
        link_container = section.find("a")
        if link_container is None:
            node_name = section.get_text().strip().replace('\xa0', ' ')
            node_number = node_name.split(" ")[0]
            if node_number[-1] == ".":
                node_number = node_number[:-1]

            if "-" in node_number:
                node_citation = f"{node_number}, MCA"
                node_number = node_number.split("-")[-1]
            
            node_type = "reserved"
            node_link = url
        else:
            node_name = link_container.get_text().strip().replace('\xa0', ' ')
            try:
                node_number = node_name.split(" ")[0]
            except:
                node_number = node_name.replace(" ", "_")
            
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            if "-" in node_number:
                node_citation = f"{node_number}, MCA"
                node_number = node_number.split("-")[-1]
            
                


            new_url = url.split("/")
            new_url.pop()
            new_url = "/".join(new_url)
            node_link = new_url + link_container['href'][1:]
            node_type = "content"
        node_level_classifier = "SECTION"

        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        if not node_citation:
            extracted_chapter = node_id.split("CHAPTER=")[1].split("/")[0]
            node_citation = f"{top_level_title}-{extracted_chapter}-{node_number}, MCA"
        
        node_tags, node_references, node_text, node_addendum = None, None, None, None

        if node_type != "reserved":
            response2 = urllib.request.urlopen(node_link)
            data2 = response2.read()      # a `bytes` object
            text2 = data2.decode('utf-8') # a `str`; 
            section_soup = BeautifulSoup(text2, features="html.parser")

            text_container = section_soup.find(class_="section-content")

            node_text = []
            
            node_addendum = section_soup.find(class_="history-content")
            if node_addendum:
                node_addendum = node_addendum.get_text().strip()

            

            node_tags = None
            node_references = None

            

            for p in text_container.find_all(recursive=False):
                txt = p.get_text().strip()
                node_text.append(txt)

            MINI_BASE = "https://leg.mt.gov/bills/mca/"
            all_links = text_container.find_all("a")
            node_references = {}
            internal = []
            for link in all_links:
                href = link['href']
                href = href.replace("../","")
                ref_link = MINI_BASE + href
                ref_text = link.get_text().strip()
                internal.append({ref_text: ref_link})
            if len(internal) > 0:
                node_references["internal"] = internal
                node_references = json.dumps(node_references)
            else:
                node_references = None

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
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
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue
            

        






def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "mt/",
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
        "mt/statutes/",
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
        "mt/",
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
    