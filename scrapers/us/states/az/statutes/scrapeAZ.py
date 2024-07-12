from bs4 import BeautifulSoup
import urllib.request
from urllib.request import Request, urlopen
import requests
import json
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
import psycopg2


 = "will"
TABLE_NAME = "az_node"
BASE_URL = "https://www.azleg.gov"
TOC_URL = "https://www.azleg.gov/arstitle/"
SKIP_TITLE = 38 # If you want to skip the first n titles, set this to n

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            print(url)
            scrape_per_title(url)
    

def scrape_per_title(url):
    req = Request(
        url=url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    webpage = urlopen(req).read()
    try:
        text = webpage.decode('utf-8')
    except UnicodeDecodeError:
        text = webpage.decode('ISO-8859-1')
    soup = BeautifulSoup(text, features="html.parser")
    #print(soup.prettify())

    title_container = soup.find(class_="topTitle")
    title_name = title_container.get_text().strip()
    top_level_title = title_name.split(" ")[1]
    og_parent = "az/statutes/"
    node_level_classifier = "TITLE"
    node_type = "structure"
    title_node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
    print(title_node_id)
    node_link = url
    node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, title_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)

    chapter_container = title_container.parent.parent.parent
    
    for i, chapter in enumerate(chapter_container.find_all(class_="accordion", recursive=False)):
        
        header = chapter.find("h5")
        link = header.find("a")
        node_name_start = link.get_text().strip()
        node_number = node_name_start.split(" ")[1]
        node_link = url + "#" + chapter['id']
        node_name_end = link.next_sibling.get_text().strip()
        node_name = f"{node_name_start} {node_name_end}"
        node_level_classifier = "CHAPTER"
        node_type = "structure"
       
        chapter_node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
        node_data = (chapter_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
        #print(node_data)
        ### INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(chapter_node_id)
        except:
            print("** Skipping:",chapter_node_id)
            continue
        

        article_container = header.next_sibling
        #print(article_container.prettify())
        for i, article in enumerate(article_container.find_all(class_="article")):
            elements = article.find_all(recursive=False)
            link_container = elements[0]
            try:
                node_name_start = link_container.get_text().strip()
                node_number = node_name_start.split(" ")[1]
                name_container = elements[1]
                node_name_end = name_container.get_text().strip()
                node_name = f"{node_name_start} {node_name_end}"

                node_level_classifier = "ARTICLE"
                node_type = "structure"
                article_node_id = f"{chapter_node_id}{node_level_classifier}={node_number}/"
                ### INSERT STRUCTURE NODE, if it's already there, skip it
                node_data = (article_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, chapter_node_id, None, None, None, None, None)
                
                try:
                    insert_node(node_data)
                    print(article_node_id)
                except:
                    print("** Skipping:",article_node_id)
                    continue
            # There is no article, goes straight from chapter to section
            except:
                article_node_id = chapter_node_id
                print("No article")
            section_container = elements[2]
            #print(section_container.prettify())
            for i, section in enumerate(section_container.find_all(recursive=False)):

                link_container = section.find(class_="colleft").find("a")
                node_name_start = link_container.get_text().strip()
                if node_name_start == "":
                    continue
                node_number = node_name_start.split("-")[1]
                node_link = BASE_URL + link_container['href']
          
                name_container = section.find(class_="colright")
                node_name_end = name_container.get_text().strip()
                node_level_classifier = "SECTION"
                node_type = "content"
                node_name = f"{node_name_start} {node_name_end}"
                node_id = f"{article_node_id}{node_level_classifier}={node_number}"

                node_text = []
                node_addendum = None
                node_citation = f"A.R.S. § {top_level_title}-{node_number}"
                node_references = None
                node_tags = None

                req2 = Request(
                    url=node_link, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                webpage2 = urlopen(req2).read()
                text2 = webpage2.decode('utf-8') # a `str`; 
                section_soup = BeautifulSoup(text2, features="html.parser")
                

                text_container = section_soup.find(class_="content-sidebar-wrap").find(class_="first")
                
                for p in text_container.find_all("p"):
                    txt = p.get_text().strip()
                    node_text.append(txt)
                
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, article_node_id, None, None, node_references, None, node_tags)
                base_node_id = node_id
    
                for i in range(2, 10):
                    try:
                        insert_node(node_data)
                        print(node_id)
                        break
                    except Exception as e:   
                        print(e)
                        node_id = base_node_id + f"-v{i}/"
                        node_type = "content_duplicate"
                        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, article_node_id, None, None, node_references, None, node_tags)
                    continue



                



    #### Get title information, Add title node
    #title_node_data = (part_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    #insert_node_ignore_duplicate(title_node_data)
    #scrape_per_part(node_link, top_level_title, part_node_id)

    #### Iterate over all next levels
        # scrape_level(url, top_level_title, node_parent)


def scrape_level(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    #### Extract structure_node information from the url
    ## Find container of this level information
    # level_container = soup.find("blah")
    # node_level_classifier = "CHAPTER"
    # node_name = "CHAPTER 1 FIND IT"
    # node_number = "1"
    # node_type = "structure"
    # node_link = "Found from somewhere"
    # node_id = f"{node_parent}{node_level_classifier}={node_number}/"


    



    # This is only for the last scrape_level
    # if node_type != "reserved":
    #     scrape_section(url, top_level_title, node_parent)

def scrape_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")


    ### FOR ADDING A CONTENT NODE, allowing duplicates
    # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    # base_node_id = node_id
    
    # for i in range(2, 10):
    #     try:
    #         insert_node(node_data)
    #         #print("Inserted!")
    #         break
    #     except Exception as e:   
    #         print(e)
    #         node_id = base_node_id + f"-v{i}/"
    #         node_type = "content_duplicate"
    #         node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    #     continue
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "az/",
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
        "az/statutes/",
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
        "az/",
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