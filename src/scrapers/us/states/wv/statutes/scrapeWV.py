import psycopg2
import os
import sys
import urllib.request
from bs4 import BeautifulSoup
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "will2"
TABLE_NAME = "wv_node"
BASE_URL = "https://code.wvlegislature.gov"

def main():
    
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < 266:
                continue
            

            if i % 2 == 0:
                url = line.strip()
            else:
                title_name = line.strip()
                scrape_per_title(url, title_name)

# node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, article_node_id, None, None, node_references, None, node_tags)

def scrape_per_title(url, title_name):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    top_level_title = title_name.split(" ")[1]
    top_level_title = top_level_title.replace(".","")
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    title_node_id = f"wv/statutes/CHAPTER={top_level_title}/"
    node_link = url
    node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, title_name, None, None, None, None, None, "wv/statutes/", None, None, None, None, None)
    print(title_node_id)
    
    insert_node_ignore_duplicate(node_data)

    article_container = soup.find(id="results-box")
    for article in article_container.find_all(class_="art-head", recursive=False):
        node_type = "structure"
        node_level_classifier = "ARTICLE"
        node_name = article.get_text()
        node_link = BASE_URL + article.find("a")['href']
        node_number = article['id'].split("-")[1]
        article_node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
        node_data = (article_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
        try:
            insert_node(node_data)
        except:
            print("** Skipping:",article_node_id)
            continue
        print(article_node_id)
        scrape_sections(node_link, article_node_id, top_level_title)


def scrape_sections(url, node_parent, top_level_title):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    section_container = soup.find(id="results-box")
    for section in section_container.find_all(class_="sec-head"):
        if 'id' in section.attrs:
            break
        node_type = "content"
        node_level_classifier = "SECTION"
        node_name = section.get_text().strip()
        if "repealed" in node_name.lower():
            node_type = "reserved"
        #print(node_name)
        node_name = node_name.replace("\n"," ")
        node_name = node_name.replace("\t"," ")
        node_name = node_name.replace("–","-")
        node_name = node_name.replace("§ ", "§")
        node_number = node_name.split(" ")[0]
        if node_number == node_name:
            node_type = "reserved"
        
        node_numbers = node_number.split("-")
        node_numbers[-1] = node_numbers[-1].replace(".","")
        node_number = node_numbers[-1]
        node_link = BASE_URL + section.find("a")['href']
        node_id = f"{node_parent}{node_level_classifier}={node_number}"
        print(node_id)
        if node_type == "reserved":
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            base_node_id = node_id
            
            for i in range(2, 10):
                try:
                    util.insert_row_to_local_db(, TABLE_NAME, node_data)
                    break
                except:
                    node_id = base_node_id + f"-v{i}/"
                    node_type = "reserved_duplicate"
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                continue
            continue
        try:
            response = urllib.request.urlopen(node_link)
            data2 = response.read()      # a `bytes` object
            text2 = data2.decode('utf-8') # a `str`; 
            section_soup = BeautifulSoup(text2, features="html.parser").body
        except:
            print("** Skipping:",node_id)
            continue
        #print(node_link)
        #print(section_soup.prettify())
        #print(section_soup.body.prettify())
        text_container = section_soup.find(id="results-box")
        all_text = text_container.find(class_="sectiontext hid")
       
        
        node_text = []
        node_citation = f"W. Va. Code § {node_numbers[0]}-{node_numbers[1]}-{node_numbers[2]}"
        node_addendum = ""
        node_references = None
        node_tags = None
        for p in all_text.find_all("p"):
            node_text.append(p.get_text().strip())

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
        base_node_id = node_id
        
        for i in range(2, 10):
            try:
                util.insert_row_to_local_db(, TABLE_NAME, node_data)
                break
            except:
                
                node_id = base_node_id + f"-v{i}/"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue


        
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "wv/",
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
        "wv/statutes/",
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
        "wv/",
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