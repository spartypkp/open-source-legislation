import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
import sys
import time
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By

 = "will2"
TABLE_NAME = "la_node"
TOC_URL = "https://www.legis.la.gov/legis/laws_Toc.aspx?folder=75&level=Parent"


def main():
    scrape()

def scrape(): 
    for i in range(6, 56):
        

        driver = webdriver.Chrome()
        driver.get(TOC_URL)
        driver.implicitly_wait(.5)
        time.sleep(1)

        
        num_element = driver.find_element(By.ID, f"ctl00_ctl00_PageBody_PageContent_ListViewTOC1_ctrl{i}_LinkButton1a")
        node_name_start = num_element.text.strip()
        top_level_title = node_name_start.split(" ")[1]
        print(f"Scraping for Title {top_level_title}...")
        
        name_element = driver.find_element(By.ID, f"ctl00_ctl00_PageBody_PageContent_ListViewTOC1_ctrl{i}_LinkButton1b")
        node_name_end = name_element.text.strip()
        title_node_name = node_name_start + " " + node_name_end

        name_element.click()
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, features="html.parser").body
        
        
        
        section_container = soup.find(id="ctl00_ctl00_PageBody_PageContent_PanelResults2")
        
        
        
        section_container = section_container.table.tbody
        
        #section_container = soup.find(id="ctl00_ctl00_PageBody_PageContent_PanelResults2")
        og_parent = "la/statutes/"
        node_parent = None
        for i, section in enumerate(section_container.find_all("tr")):

            all_tds = section.find_all("td")
            link_container = all_tds[0]
            name_container = all_tds[1]
            node_name = name_container.get_text().strip()
            node_citation = link_container.get_text().strip()
            node_number = node_citation.split(" ")[1]
            node_link = "https://www.legis.la.gov/legis/" + link_container.find("a")['href']
            node_type = "content"
            
            
            if node_parent is None:
                node_level_classifier = "TITLE"
                node_type = "structure"
                
                node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
                print(node_id)
                node_parent = node_id
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, TOC_URL, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
                insert_node_ignore_duplicate(node_data)
                node_type = "content"
            
            if ":" not in node_citation:
                continue
            
            node_number = node_number.split(":")[1]
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            node_level_classifier = "SECTION"
            if "Repealed" in node_name:
                node_type = "reserved"
            elif node_type == "reserved":
                print(node_id)
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, TOC_URL, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)

                base_node_id = node_id
                
                for i in range(2, 10):
                    try:
                        insert_node(node_data)
                        #print("Inserted!")
                        break
                    except Exception as e:   
                        print(e)
                        node_id = base_node_id + f"-v{i}/"
                        node_type = "reserved_duplicate"
                        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, TOC_URL, None, title_node_name, None, None, None, None, None, og_parent, None, None, None, None, None)

                    continue
            else:
        
                response2 = urllib.request.urlopen(node_link)
                data2 = response2.read()      # a `bytes` object
                text2 = data2.decode('utf-8') # a `str`; 
                section_soup = BeautifulSoup(text2, features="html.parser")
                text_container = section_soup.find(id="ctl00_PageBody_LabelDocument")

                node_text = []

                for p in text_container.find_all("p"):
                    if 'style' in p.attrs and p.attrs['style']=="text-align: center":
                        continue
                    #print(p)
                    txt = p.get_text().strip()
                    node_text.append(txt)
            
                
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
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
                        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    continue
        
       

                

                


    


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "la/",
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
        "la/statutes/",
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
        "la/",
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