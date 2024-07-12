import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
import time
import json
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re

 = "will2"
TABLE_NAME = "tx_node"
BASE_URL = "https://statutes.capitol.texas.gov"
TOC_URL = "https://statutes.capitol.texas.gov/Index.aspx"
SKIP_TITLE = 30 # If you want to skip the first n titles, set this to n
RESERVED_KEYWORDS = ["Repealed"]

CODE_MAP ={
    "AGRICULTURE CODE":"AG",
    "ALCOHOLIC BEVERAGE CODE":"AL",
    "BUSINESS AND COMMERCE CODE":"BC",
    "BUSINESS ORGANIZATIONS CODE":"BO",
    "TEXAS CONSTITUTION": "CN",
    "CIVIL PRACTICE AND REMEDIES CODE":"CP",
    "CODE OF CRIMINAL PROCEDURE":"CR",
    "VERNON'S CIVIL STATUTES":"CV",
    "EDUCATION CODE":"ED",
    "ELECTION CODE": "EL",
    "ESTATES CODE":"ES",
    "FAMILY CODE":"FA",
    "FINANCE CODE":"FI",
    "GOVERNMENT CODE":"GV",
    "HUMAN RESOURCES CODE":"HR",
    "HEALTH AND SAFETY CODE":"HS",
    "INSURANCE CODE - NOT CODIFIED":"I1",
    "INSURANCE CODE": "IN",
    "LABOR CODE": "LA",
    "LOCAL GOVERNMENT CODE":"LG",
    "NATURAL RESOURCES CODE":"NR",
    "OCCUPATIONS CODE":"OC",
    "PENAL CODE":"PE",
    "PROPERTY CODE":"PR",
    "PARKS AND WILDLIFE CODE":"PW",
    "SPECIAL DISTRICT LOCAL LAWS CODE":"SD",
    "TRANSPORTATION CODE":"TN",
    "TAX CODE":"TX",
    "UTILITIES CODE":"UT",
    "WATER CODE":"WA",
    "AUXILIARY WATER LAWS":"WL",
}

def main():
    insert_jurisdiction_and_corpus_node()
    # scrape_constitution
    scrape_all_titles()



def scrape_all_titles():
    
    driver = webdriver.Chrome()
    driver.get(TOC_URL)
    driver.implicitly_wait(2)

    # Get the container of all titles
    titles_container = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_NavTree")
    titles_table = titles_container.find_elements(By.TAG_NAME, "table")[1]

    # Open the titles table
    titles_table.click()
    time.sleep(4)
    

    og_parent = "tx/statutes/"
    for i in range(SKIP_TITLE, 31):
        soup = BeautifulSoup(driver.page_source, features="html.parser").body
        title_soup = soup.find(id="ctl00_ContentPlaceHolder1_NavTreen1Nodes")
        title_table = title_soup.find_all("table", recursive=False)[i]
        #print(title_table.prettify())

        name_container = title_table.tbody.tr.find_all("td", recursive=False)[-1]
        node_name = name_container.get_text().strip()
        node_level_classifier = "CODE"
       
        if node_name == "PROBATE CODE":
            continue
        top_level_title = CODE_MAP[node_name]
        node_type = "structure"
        node_link = TOC_URL
        node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
        print(node_id)
        
        title_node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(title_node_data)

        a_tag = name_container.find("a")
        title_table_id = a_tag.get("id").replace("Treet", "Treen") + "Nodes"
        print(title_table_id)
        #print(title_table_id)
        title_table_selenium = driver.find_element(By.ID, a_tag.get("id"))
        # ctl00_ContentPlaceHolder1_NavTreet2
        # Scroll to the title table
        driver.execute_script("arguments[0].scrollIntoView();", title_table_selenium)
        time.sleep(2)
        title_table_selenium.click()
        time.sleep(10)
        # ctl00_ContentPlaceHolder1_NavTreen1Nodes
        

        # Get the title table one last time, tree HTML loaded
        soup = BeautifulSoup(driver.page_source, features="html.parser").body      
        level_container = soup.find(id=f"{title_table_id}")
        if level_container.find_all(recursive=False)[0].find(class_="PDFicon") is not None:
            scrape_sections(level_container, top_level_title, node_id)
        else:
            scrape_level(level_container, top_level_title, node_id)


        driver = webdriver.Chrome()
        driver.get(TOC_URL)
        driver.implicitly_wait(2)

        # Get the container of all titles
        titles_container = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_NavTree")
        titles_table = titles_container.find_elements(By.TAG_NAME, "table")[1]

        # Open the titles table
        titles_table.click()
        time.sleep(4)
        

        
    

def scrape_level(level_container, top_level_title, node_parent):
    


    all_child_containers = level_container.find_all(recursive=False)
    for i in range(0, len(all_child_containers), 2):
        
        current_level = all_child_containers[i]
        node_name = current_level.get_text().strip()
        node_level_classifier = node_name.split(" ")[0]
        node_number = node_name.split(" ")[1]
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        node_type = "structure"
        node_link = TOC_URL
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        #print(node_data)
        try:
            next_level_container = all_child_containers[i+1]
        except:
            node_type = "reserved"

         ## INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        
        if node_type != "reserved":
            if next_level_container.find_all(recursive=False)[0].find(class_="PDFicon") is not None:
                scrape_sections(next_level_container, top_level_title, node_id)
            else:
                scrape_level(next_level_container, top_level_title, node_id)





def scrape_sections(level_container, top_level_title, node_parent):
    
    for i, child in enumerate(level_container.find_all(recursive=False)):
        
        all_a_tags = child.find_all("a")
        #print(len(all_a_tags))
        name_tag = all_a_tags[1]
        #print(name_tag.prettify())
        node_name = name_tag.get_text().strip()
        node_level_classifier = node_name.split(" ")[0]
        node_number = node_name.split(" ")[1]
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        node_type = "structure"
        link_tag = all_a_tags[3]
        node_link = link_tag.get("href")

        chapter_node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        node_data = (chapter_node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        
         ## INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(chapter_node_id)
        except:
            print("** Skipping:",chapter_node_id)
            continue


        
        file_target = node_link.split("/")[-1]
        directory_target = file_target.split(".")[0] + ".htm"

        file_path = f"{DIR}/data/{directory_target}/{file_target}"
        
        with open(file_path, "r") as file:
            section_soup = BeautifulSoup(file.read(), features="html.parser")
            

            all_p_tags_raw = section_soup.find_all("p")
            all_p_tags = []
            # Remove all tags that have class="center"
            for p in all_p_tags_raw:
                print(p.prettify())
                print(p.get("class"))
                if p.get("class") is not None:
                    if p.get("class") == []:
                        all_p_tags.append(p)
                        continue
                    if p.get("class")[0] != "center":
                        all_p_tags.append(p)

            node_id = None

            for p in all_p_tags:
                print(p.prettify())
                txt = re.sub(r'\s+', ' ', p.get_text().strip())
                if txt == "":
                    continue
                print(txt)

                if txt[0:5] == "Sec. " or txt[0:5] == "Art. ":
                    print("== New Section or Article ==")
                    if node_id is not None:
                        print("== Inserting Previous Section ==")
                        if len(internal) > 0:
                            node_references['internal'] = internal
                        if len(external) > 0:
                            node_references['external'] = external
                        if node_references == {}:
                            node_references = None
                        else:
                            node_references = json.dumps(node_references)
                        section_node_link = node_link + f"#{node_number}"
                         ### FOR ADDING A CONTENT NODE, allowing duplicates
                        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_node_link, node_addendum, node_name, None, None, None, None, None, chapter_node_id, None, None, node_references, None, node_tags)
                        base_node_id = node_id

                        for word in RESERVED_KEYWORDS:
                            if word in node_name:
                                node_type = "reserved"
                                break
                            
                        
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
                                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
                            continue
                        node_references = {}
                        node_tags = None
                        internal = []
                        external= []
                        
                    # Find the index of the 4th occurence of "." in txt
                    # This is the index of the end of the section number
                    node_number = txt.split(" ")[1]
                    index = node_number.count(".") + 1
                    try:
                        node_name_index = [pos for pos, char in enumerate(txt) if char == '.'][index]
                    except:
                        node_name_index = len(txt) - 1
                    node_name = txt[0: node_name_index + 1]
                    
                    if node_number[-1] == ".":
                        node_number = node_number[:-1]
                    
                    full_name = ""
                    for k,v in CODE_MAP.items():
                        if v == top_level_title:
                            full_name = k
                            break

                    # Convert full_name, which is in all caps, to camel case (TEST STRING -> Test String)
                    full_name = " ".join([word.capitalize() for word in full_name.split(" ")])
                    
                    node_citation =f"Tex. {full_name} § {node_number}"
                    node_addendum = ""
                    if txt[0:5] == "Art. ":
                        node_level_classifier = "ARTICLE"
                    else:
                        node_level_classifier = "SECTION"
                    node_text = []

                    node_text.append(txt[node_name_index + 1:])
                    node_type = "content"
                    node_references = {}
                    node_tags = None
                    internal = []
                    external= []
                    node_id = f"{chapter_node_id}{node_level_classifier}={node_number}"
                    addendum_found = False
                    
                elif 'style' in p.attrs and not addendum_found:
                    print("== Style Case ==")
                    node_text.append(txt)
                    
                else:
                    print("== Default, Addendum ==")
                    node_addendum += txt + "\n"
                    addendum_found = True
                    
                
                for a in p.find_all("a"):
                    if a.get("href") is not None:
                        citation_link = a.get("href")
                        citation_number = a.get_text().strip()
                        # print(a.prettify())
                        # print(citation_number)
                        try:
                            left_index = a.previous_sibling.text.rindex("(")
                            left_text = a.previous_sibling.text[left_index:]

                            right_index = a.next_sibling.text.index(")")
                            right_text = a.next_sibling.text[:right_index + 1]
                        except:
                            
                            try:
                                left_text = a.previous_sibling.text[len(a.previous_sibling.text)-50:]
                            except:
                                left_text = ""
                            try:
                                right_text = a.previous_sibling.text[:50]
                            except:
                                right_text = ""
                        
                        citation_text = left_text + citation_number + right_text
                        temp = {"citation_link": citation_link, "citation_text": citation_text, "citation_number": citation_number}
                        if "https://statutes.capitol.texas.gov" in citation_link:
                            internal.append(temp)
                        else:
                            external.append(temp)

            print(node_id)
            if node_id is None:
                continue
            print(node_references)
            if len(internal) > 0:
                node_references['internal'] = internal
            if len(external) > 0:
                node_references['external'] = external
            if node_references == {}:
                node_references = None
            else:
                node_references = json.dumps(node_references)
                ### FOR ADDING A CONTENT NODE, allowing duplicates

            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved"
                    break
            section_node_link = node_link + f"#{node_number}"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_node_link, node_addendum, node_name, None, None, None, None, None, chapter_node_id, None, None, node_references, None, node_tags)
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
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_node_link, node_addendum, node_name, None, None, None, None, None, chapter_node_id, None, None, node_references, None, node_tags)
                continue


            
                    
                


            




   
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "tx/",
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
        "tx/statutes/",
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
        "tx/",
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