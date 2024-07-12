import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import json
from bs4.element import Tag



RESERVED_KEYWORDS = ["repealed by", "renumbered", "Repealed", "Renumbered" ]

 = "will2"
TABLE_NAME = "or_node"
BASE_URL = "https://www.oregonlegislature.gov"
TOC_URL = "https://www.oregonlegislature.gov/bills_laws/pages/ors.aspx"
SKIP_TITLE = 0# If you want to skip the first n titles, set this to n

def main():
    insert_jurisdiction_and_corpus_node()
    scrape_titles()
    

def scrape_titles():
    
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)
    og_parent = "or/statutes/"
    
    # 144 total containers
    for i in range(2, 144):

        #print(i)
        container = DRIVER.find_element(By.ID, "MSOZoneCell_WebPartWPQ8")
        titles_containers = container.find_elements(By.TAG_NAME, "tbody")
        # Get the title element by index
        title = titles_containers[i]
        DRIVER.execute_script("arguments[0].scrollIntoView();", title)

        title_soup = BeautifulSoup(title.get_attribute("innerHTML"), features="html.parser")
        title_soup_weird = BeautifulSoup(title.get_attribute("outerHTML"), features="html.parser").find("tbody")
        node_name = title_soup.get_text().strip()
        
        
        container_id = title_soup_weird.attrs['id']
        #print(container_id)
        num_underscores = container_id.count("_")
        #print(num_underscores)
        # Skip doing anything for volume
        if num_underscores > 1:
            # Handle chapters separately 
            if num_underscores == 3:
                all_chapters = title_soup.find_all("tr", recursive=False)
                for i, chapter_container in enumerate(all_chapters):
                    #print(chapter_container.prettify())
                    all_tds = chapter_container.find_all("td", recursive=False)
                    link_container = all_tds[0].find("a")
                    name_container = all_tds[1]


                    node_name_start = link_container.get_text().strip()
                    node_number_raw = node_name_start.split(" ")[1]
                    node_number = node_number_raw
                    node_link = BASE_URL + link_container['href']

                    node_name_end = name_container.get_text().strip()
                    if node_name_end == "(Former Provisions)":
                        node_type = "reserved"
                    else:
                        node_type = "structure"
                    
                    node_name = f"{node_name_start} {node_name_end}"
                    

                    node_level_classifier = "CHAPTER"
                    node_id = f"{title_node_id}{node_level_classifier}={node_number}/"
                    chapter_node_data =  (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, title_node_id, None, None, None, None, None)
                    try:
                        insert_node(chapter_node_data)
                        print(node_id)
                    except:
                        print("** Skipping:",node_id)
                        continue

                    if node_type != "reserved":
                        #print(node_number)
                        node_ch = ""
                        if (node_number[-1].isalpha()):
                            node_ch = node_number[-1]
                            node_number = node_number[:-1]
                        node_number = str(int(node_number))
                        scrape_chapter(node_link, top_level_title, node_id, node_number, node_ch)

                # Don't click any chapter links
                continue

            # Handle Titles 
            else:

                node_number_raw = node_name.split(":")[1].strip()
                node_number = node_number_raw.split(" ")[0]
                if node_number[-1] == ".":
                    node_number = node_number[:-1]
                
                node_type = "structure"
                node_level_classifier = "TITLE"
                node_link = TOC_URL
                title_node_id = f"{og_parent}{node_level_classifier}={node_number}/"
                top_level_title = node_number

                node_data =  (title_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
                try:
                    insert_node(node_data)
                    print(title_node_id)
                except:
                    print("** Skipping:",title_node_id)
                    continue




        
        link_container = title.find_element(By.TAG_NAME, "a")
        link_container.click()
        
        time.sleep(1)



def scrape_chapter(url, top_level_title, node_parent, chapter_num, chapter_ch):
    # Remove all non-numeric characters from chapter_num
    
    
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', errors="ignore") # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    

    all_sections = soup.find_all("b")
    
    for i, section_tag in enumerate(all_sections):

        
        node_name = get_text_clean(section_tag)
        
        if f"{chapter_num}{chapter_ch}." not in node_name[0:5]:
            continue
        
        node_number_raw = node_name.split(" ")[0].replace(",","")
        node_citation = f"ORS {node_number_raw}"
        node_number = node_number_raw.split(".")[1]

        node_level_classifier = "SECTION"
        node_type = "content"
        node_link = url
        node_id = f"{node_parent}{node_level_classifier}={node_number}"

        node_text = None
        node_addendum = None
        node_references = None
        node_tags = {}
        for word in RESERVED_KEYWORDS:
            if word in node_name.lower():
                node_type = "reserved"
                break

        if node_type != "reserved":
            node_text = []
            p_tag = section_tag.parent
           
            node_text.append(get_text_clean(p_tag))
            for p_tag in p_tag.next_siblings:
                
                if not isinstance(p_tag, Tag):
                    continue
                txt = get_text_clean(p_tag)

                
                # Bold element found, investigate
                if p_tag.find("b") is not None:
                    #print("Found B element")
                    b_txt = p_tag.find("b").get_text().strip()
                    
                    
                    # New section found, break
                    if f"{chapter_num}." in b_txt[0:10]:
                        break
                    # Weird bold part of current section
                    node_tags[b_txt] = txt
                    
                    continue
                if txt != "":
                    node_text.append(txt)
                

            
            possible_addendum = node_text[-1]
            # Find any text within [] and set it as addendum
            if "[" in possible_addendum and "]" in possible_addendum:
                node_addendum = possible_addendum.split("[")[1].split("]")[0]
            
            for word in RESERVED_KEYWORDS:
                if word in node_text[0]:
                    node_type = "reserved"
                    node_text = [node_text[0]]
                    break
        
        if node_tags != {}:
            node_tags = json.dumps(node_tags)
        else:
            node_tags = None
        
        
        ### FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
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
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            continue




    


# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "or/",
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
        "or/statutes/",
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
        "or/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)





def get_text_clean(element):
    return element.get_text().replace('\xa0', '').replace('\r', ' ').replace('\n', '').strip()

def print_element_to_file(element, filename):
    with open(f"{DIR}/DATA/{filename}.txt", "w") as f:
        f.write(element.prettify())
    f.close()
if __name__ == "__main__":
    main()