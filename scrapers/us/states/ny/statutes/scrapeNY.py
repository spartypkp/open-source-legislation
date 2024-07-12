import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

 = "will"
TABLE_NAME = "ny_node"

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < 78:
                continue
            
            url = line.strip()
            scrape_per_title(url)
            


def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    og_parent = "ny/statutes/"
    container = soup.find(class_="nys-openleg-result-container")
    chapter_container = container.find(class_="nys-openleg-head-container")
    node_name_start = chapter_container.find(class_="nys-openleg-result-title-headline").get_text().strip()
    top_level_title = url.split("/")[-1]
    node_name_end = chapter_container.find(class_="nys-openleg-result-title-short").get_text().strip()
    title_node_name = node_name_start + " " + node_name_end
    title_node_type = "structure"
    title_node_level_classifier = "CHAPTER"
    title_node_link = url
    title_node_id = f"{og_parent}{title_node_level_classifier}={top_level_title}/"
    print(title_node_id)
    node_data = (title_node_id, top_level_title, title_node_type, title_node_level_classifier, None, None, None, title_node_link, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)

    article_container = container.find(class_="nys-openleg-content-container")
    for i, article in enumerate(article_container.find_all(class_="nys-openleg-result-item-container")):
        link = article.find("a")
        node_link = link['href']
        node_level_classifier = "ARTICLE"
        node_type = "structure"
        node_name_start = link.find(class_="nys-openleg-result-item-name").get_text().strip()
        node_name_end = link.find(class_="nys-openleg-result-item-description").get_text().strip()
        node_number = node_name_start.split(" ")[1]
        node_name = node_name_start + " " + node_name_end
        node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
        
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print(" ** Skipping: ", node_id)
            continue
        scrape_sections(node_link, top_level_title, node_id)

def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    container = soup.find(class_="nys-openleg-result-container")
    section_container = container.find(class_="nys-openleg-content-container")
    
    for i, section in enumerate(section_container.find_all(class_="nys-openleg-result-item-container")):
        link = section.find("a")
        node_link = link['href']
        node_level_classifier = "SECTION"
        node_type = "content"
        node_name_start = link.find(class_="nys-openleg-result-item-name").get_text().strip()
       
        node_name_end = link.find(class_="nys-openleg-result-item-description")
        if node_name_end is None:
            node_name_end = ""
        else:
            node_name_end = node_name_end.get_text().strip()

        node_number = node_name_start.split(" ")[1]
        node_name = node_name_start + " " + node_name_end
        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        print(node_id)
        node_text = []
        node_addendum = ""
        node_citation = f"N.Y. {top_level_title} § {node_number}"
        node_references = None
        node_tags = None

        if "TITLE" in node_name_start:
            node_level_classifier = "TITLE"
            node_type = "structure"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            scrape_sections(node_link, top_level_title, node_parent)
        else:

            response2 = urllib.request.urlopen(node_link)
            data2 = response2.read()      # a `bytes` object
            text2 = data2.decode('utf-8') # a `str`; 
            soup2 = BeautifulSoup(text2, features="html.parser")

            node_addendum = soup2.find(class_="nys-openleg-history-published")
            if node_addendum is not None:
                cont = node_addendum.children
                for child in cont:
                    node_addendum = child.get_text().strip()
                    break
                

            result_container = soup2.find(class_="nys-openleg-result-container")
            text_container = result_container.find(class_="nys-openleg-result-text")
            if text_container is not None:
            
                for p in text_container.children:
                    
                    txt = p.get_text().strip()
                    if txt == "":
                        continue
                    if txt == "<br/>":
                        node_text[-1] += "\n"
                        continue

                node_text.append(txt)
            
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
        "ny/",
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
        "ny/statutes/",
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
        "ny/",
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