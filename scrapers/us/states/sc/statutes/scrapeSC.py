import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from bs4.element import Tag
import time


 = "will2"
TABLE_NAME = "sc_node"
BASE_URL = "https://www.scstatehouse.gov"
TOC_URL = "https://www.scstatehouse.gov/code/statmast.php"
SKIP_TITLE = 48 #40 # If you want to skip the first n titles, set this to n
RESERVED_KEYWORDS = ["REPEALED"]

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_per_title(url)
    

def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    title_container = soup.find(class_="barheader")
    node_name = title_container.contents[-1].text.strip()
    
    
    top_level_title = node_name.split(" ")[1]
    node_level_classifier = "TITLE"
    node_link = url
    node_type = "structure"
    node_id = f"sc/statutes/{node_level_classifier}={top_level_title}/"


    ### Get title information, Add title node
    title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, "sc/statutes/", None, None, None, None, None)
    insert_node_ignore_duplicate(title_node_data)
   
    level_container = soup.find(id="contentsection")
    scrape_level(level_container, top_level_title, node_id)


def scrape_level(level_container, top_level_title, node_parent):
    
    
    for i, tr in enumerate(level_container.find_all("tr")):
        all_tds = tr.find_all("td", recursive=True)
        #print(tr.prettify())
        name_container = all_tds[0]
        
        node_name = name_container.get_text().strip()
        node_level_classifier = node_name.split(" ")[0]
        node_number = node_name.split(" ")[1]

        link_container = all_tds[1]
        node_link = BASE_URL + link_container.a['href']
        node_type = "structure"
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"

        for word in RESERVED_KEYWORDS:
            if word in node_name:
                node_type = "reserved"
                break
        node_data =  (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        ## INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        
        if node_type != "reserved":
            scrape_sections(node_link, top_level_title, node_id)



    # This is only for the last scrape_level
    # if node_type != "reserved":
    #     scrape_section(url, top_level_title, node_parent)
            

    # Title, Chapter, Article, Section

def scrape_sections(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors='ignore') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")


    title_container = soup.find(id="contentsection")

    chapter_index = -2
    article_index = -2
    subarticle_index = -2
    
    items_seen = 0
    all_elements = []
    current_article = None
    current_subarticle = None

    for i, element in enumerate(title_container.contents):
        items_seen += 1
        
        if not isinstance(element, Tag):
            if str(element).strip() != "":
                all_elements.append(str(element).strip())
            continue
        if element.name == "br":
            continue
        txt = element.get_text().strip()
        
        if element.name == "div":
            style = element.attrs['style']
            
            if style:
                style = style[0]
                if "Title" in txt:
                    continue
                if "CHAPTER" in txt:
                    chapter_index = i
                    continue

                if i == chapter_index + 3:
                    
                    chapter_index = -2
                    continue

                if "ARTICLE" in txt:
                    article_index = i
                    current_article = txt
                    continue

                if i == article_index + 3:
                    new_div = soup.new_tag(name="div")
                    new_div.string = f"{current_article} {txt}"
                    
                    all_elements.append(new_div)
                    
                    article_index = -2
                    continue

                if "Subarticle" in txt:
                    subarticle_index = i
                    current_subarticle = txt
                    continue

                if i == subarticle_index + 3:
                    new_h1 = soup.new_tag(name="h1")
                    new_h1.string = f"{current_subarticle} {txt}"
                    
                    all_elements.append(new_h1)
                    
                    subarticle_index = -2
                    continue

        if element.name == "span":
            #print(element)
            if element.find("a"):
                
                if '<br' in element.find("a")['name']:
                    
                    continue
            else:
                continue
            
        all_elements.append(element)
        


    #print("Items Seen: ", items_seen)
    #print("Length of Filtered ELements: ", len(all_elements))
    

    current_section_created = False
    last_article = node_parent
    last_section_index = -5
    node_name = None
    for i, element in enumerate(all_elements):
        #print(i)
        if isinstance(element, Tag):
            #print("TAG: ", element.name)
            
            if element.name == "div":
                if current_section_created:

                    for word in RESERVED_KEYWORDS:
                        if word in node_name:
                            node_type = "reserved"
                            break
                    ## FOR ADDING A CONTENT NODE, allowing duplicates
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                    base_node_id = node_id
                    
                    for j in range(2, 10):
                        try:
                            insert_node(node_data)
                            print(node_id)
                            break
                        except Exception as e:   
                            print(e)
                            node_id = base_node_id + f"-v{j}"
                            node_type = "content_duplicate"
                            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                        continue
                    current_section_created = False



                article_node_name = element.get_text().strip()
                article_node_level_classifier = "ARTICLE"
                article_node_number = article_node_name.split(" ")[1]
                node_type = "structure"
                article_node_id = f"{node_parent}{article_node_level_classifier}={article_node_number}/"
                node_link = url
                node_data =  (article_node_id, top_level_title, node_type, article_node_level_classifier, None, None, None, node_link, None, article_node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                last_article = article_node_id
                

                try:
                    insert_node(node_data)
                    print(article_node_id)
                except:
                    print("** Skipping:",article_node_id)
                    continue
                continue
            elif element.name == "span":

                if current_section_created:

                    for word in RESERVED_KEYWORDS:
                        if word in node_name:
                            node_type = "reserved"
                            break
                    ## FOR ADDING A CONTENT NODE, allowing duplicates
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                    base_node_id = node_id
                    
                    for j in range(2, 10):
                        try:
                            insert_node(node_data)
                            print(node_id)
                            break
                        except Exception as e:   
                            print(e)
                            node_id = base_node_id + f"-v{j}"
                            node_type = "content_duplicate"
                            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                        continue
                    current_section_created = False
                

                node_name = element.get_text().strip() + " "
                
                #print(f"Initial Node Name: {node_name}")
                node_number = node_name.split(" ")[1]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]

                node_citation = f"S.C. Code § {node_number}"
                node_number = node_number.split("-")[-1]
                node_link = url + "#" + element.find("a")['name']
                node_level_classifier = "SECTION"
                node_type = "content"
                node_id = f"{last_article}{node_level_classifier}={node_number}"
                node_text = []
                node_addendum = ""
                node_tags = None
                node_references = None
                last_section_index = i
                current_section_created = True
            elif element.name == "h1":
                if current_section_created:

                    for word in RESERVED_KEYWORDS:
                        if word in node_name:
                            node_type = "reserved"
                            break
                    ## FOR ADDING A CONTENT NODE, allowing duplicates
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                    base_node_id = node_id
                    
                    for j in range(2, 10):
                        try:
                            insert_node(node_data)
                            print(node_id)
                            break
                        except Exception as e:   
                            print(e)
                            node_id = base_node_id + f"-v{j}"
                            node_type = "content_duplicate"
                            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
                        continue
                    current_section_created = False



                subarticle_node_name = element.get_text().strip()
                subarticle_node_level_classifier = "SUBARTICLE"
                subarticle_node_number = subarticle_node_name.split(" ")[1]
                node_type = "structure"
                subarticle_node_id = f"{article_node_id}{subarticle_node_level_classifier}={subarticle_node_number}/"
                node_link = url
                node_data =  (subarticle_node_id, top_level_title, node_type, subarticle_node_level_classifier, None, None, None, node_link, None, subarticle_node_name, None, None, None, None, None, article_node_id, None, None, None, None, None)
                last_article = subarticle_node_id
                
                
        else:
            if not current_section_created:
                continue
            #print(element)
            #print("Last Section Index: ", last_section_index)
            if element.strip() == "":
                continue
            if i-1 == last_section_index:
                node_name += element
            elif "HISTORY:" in element:
                node_addendum = element
            else:
                node_text.append(element)

    if node_name is not None:

        for word in RESERVED_KEYWORDS:
            if word in node_name:
                node_type = "reserved"
                break

        ## FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
        base_node_id = node_id
        
        for j in range(2, 10):
            try:
                insert_node(node_data)
                print(node_id)
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{j}"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, last_article, None, None, node_references, None, node_tags)
            continue


# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "sc/",
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
        "sc/statutes/",
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
        "sc/",
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