from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
import requests
import json
import re
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import psycopg2
import sys
import time
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


 = "will2"
TABLE_NAME = "nm_node"
BASE_URL = "https://nmonesource.com"
DRIVER = None
RESRVED_KEYWORD = ["Repealed", "Reserved"]

# 45, 46B, 54, 
# title, subtitle, chapter, subchapter, part, subpart, division, subdivision
# NUM DONE = 1
TITLE_NUM = 0

def reset_page():    
    container = DRIVER.find_element(By.CLASS_NAME, "toc-expand-all")
    btn = container.find_element(By.TAG_NAME, "button")
    btn.click()
    time.sleep(1)
    container = DRIVER.find_element(By.CLASS_NAME, "toc-collapse-all")
    btn = container.find_element(By.TAG_NAME, "button")
    btn.click()


def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if (i < TITLE_NUM):
                continue
            #print(line)
            
            
            
            scrape_title(line.strip())

def scrape_title(url):
    global DRIVER
    #Example url: https://nmonesource.com/nmos/nmsa/en/item/4351/index.do

    # Load page with selenium
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(.5)
    
    # Find list of all articles, within the sidebar
    
    iframe = driver.find_element(By.ID, "decisia-iframe")
    driver.switch_to.frame(iframe)
    DRIVER = driver

    og_parent = "nm/statutes/"
    container = driver.find_element(By.ID, "decisia-document-header")
    title_container = container.find_element(By.CLASS_NAME, "title")
    node_name = title_container.text.strip()
    top_level_title = node_name.split(" ")[1]
    node_level_classifier = "CHAPTER"
    node_type = "structure"
    node_link = url
    node_id = f"{og_parent}CHAPTER={top_level_title}/"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, og_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(node_data)
    

    level_container = driver.find_element(By.ID, "toc-display-inner").find_element(By.TAG_NAME, "ul")
    scrape_level(level_container, node_link, top_level_title, node_id)



def scrape_level(level_container, url, top_level_title, node_parent):
    
    all_elements = level_container.find_elements(By.XPATH, "./li")
    for i, element in enumerate(all_elements):
        
        time.sleep(1)
        #print(element.get_attribute("class"))
        if "parent" not in element.get_attribute("class"):
            continue
        name_container = element.find_element(By.CLASS_NAME, "toc-heading-2").find_element(By.CLASS_NAME, "toc-title")
        data_anchor_text = element.get_attribute("data-anchor-text")

        section_a_link = click_and_get_containers(name_container, data_anchor_text)
    
        annotation_container = element.find_element(By.CLASS_NAME, "toc-branch").find_element(By.XPATH, "./li")
        annotation_data_anchor_text = annotation_container.get_attribute("data-anchor-text")
        annotation_container = annotation_container.find_element(By.CLASS_NAME, "toc-title")
        node_name = name_container.text.strip()
        print(node_name)
       
        # Section found!
        if node_name.count("-") >= 2:
            node_level_classifier = "SECTION"
            node_number = node_name.split(" ")
            if node_number[0][-1] == ".":
                node_number[0] = node_number[0][:-1]
            node_citation = node_number[0]
            node_number = node_number[0].split("-")[-1]
            node_type = "content"
            node_link = url + f"#{node_citation}"
            node_id = f"{node_parent}{node_level_classifier}={node_number}"
            print(node_link)
                        

            node_addendum = ""
            node_citation = f"NMSA 1978, § {node_citation}"
            node_text = []
            node_references = {}
            node_tags = {}
            
            internal = []
            external = []
            internal_addendum = []
            external_addendum = []
            internal_annotation = []
            external_annotation = []

            for word in RESRVED_KEYWORD:
                if word in node_name:
                    node_type = "reserved"
                    break
            if node_type != "reserved":


                # Get all siblings of the parent HTML Element
                all_children_soup = get_all_children_soup(section_a_link)
                print(type(all_children_soup))
                print(len(all_children_soup))

                # Find all text p tags until the next h6 tag
                all_text_p_tags = []
                while True:
                    if len(all_children_soup) == 0:
                        break
                    if all_children_soup[0].tag_name == "h6":
                        break
                    print(all_children_soup[0].prettify())
                    all_text_p_tags.append(all_children_soup.pop(0))


                # Find all annotation p tags until the next h5 tag
                all_annotation_p_tags = []
                try:
                    all_children_soup.pop(0)
                except:
                    # Click the annotation container, reget all siblings of the parent HTML Element
                    click_with_wait_and_retry(annotation_container)
                    # Get the first following sibling of the header WebElement
                    wait = WebDriverWait(DRIVER, 10)
                    print(annotation_data_anchor_text)
                    annotation_a_link = wait.until(EC.presence_of_element_located((By.ID, f"{annotation_data_anchor_text}")))
                    all_children_soup = get_all_children_soup(annotation_a_link)


                while True:
                    if len(all_children_soup) == 0:
                        break
                    if all_children_soup[0].tag_name == "h6":
                        break
                    all_annotation_p_tags.append(all_children_soup.pop(0))
                
            
                addendum_found = False
                for p in all_text_p_tags:
                    txt = p.get_text().strip()

                    if p['class'] is not None:
                        
                        if p['class'][0] == "history":
                            node_addendum += txt + '\n'
                            addendum_found = True
                            continue
                    
                    if addendum_found:
                        node_addendum += txt + '\n'
                        all_a = p.find_all("a")
                        for a in all_a:
                            try:
                                href = a['href']
                            except:
                                continue
                            if "-" in href:
                                internal_addendum.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                            else:
                                external_addendum.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                        continue
                    else:
                        node_text.append(txt)
                        all_a = p.find_all("a")
                        for a in all_a:
                            try:
                                href = a['href']
                            except:
                                continue
                            if "-" in href:
                                internal.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                            else:
                                external.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                        continue
    
                base = "annotations"
                for p in all_annotation_p_tags:
                    txt = p.get_text().strip()
                    try:
                        tag = p.find("b").get_text().strip()
                    except:
                        tag=base
                        
                    if tag not in node_tags:
                        node_tags[tag] = []
                    node_tags[tag].append(txt)

                    all_a = p.find_all("a")
                    for a in all_a:
                        try:
                            href = a['href']
                        except:
                            continue
                        if "-" in href:
                            internal_annotation.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                        else:
                            external_annotation.append({"citation": a.get_text(), "link": "https://nmonesource.com"+href})
                    
                    
            if len(internal) > 0:
                node_references["internal"] = internal
            if len(external) > 0:
                node_references["external"] = external

            addendum_references = {}
            annotation_references = {}
            if len(internal_addendum) > 0:
                addendum_references["internal"] = internal_addendum
            if len(external_addendum) > 0:
                addendum_references["external"] = external_addendum
            if len(internal_annotation) > 0:
                annotation_references["internal"] = internal_annotation
            if len(external_annotation) > 0:
                annotation_references["external"] = external_annotation
            
            if len(addendum_references.keys()) > 0:
                node_tags["addendum_references"] = addendum_references
            if len(annotation_references.keys()) > 0:
                node_tags["annotation_references"] = annotation_references
            if len(node_tags.keys()) == 0:
                node_tags = None
            else:
                node_tags = json.dumps(node_tags)

            if len(node_references.keys()) == 0:
                node_references = None
            else:
                node_references = json.dumps(node_references)

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

            
            section_close_container = element.find_element(By.CLASS_NAME, "toc-heading-2").find_element(By.CLASS_NAME, "toc-parent-indicator")
            click_with_wait_and_retry(section_close_container)
            continue
                        

        node_level_classifier = node_name.split(" ")[0].upper()
        node_number = node_name.split(" ")[1]
        node_type = "structure"
        node_link_id = node_name.replace(" ", "_").replace(f"_{node_number}_",f"_{node_number}__")
        node_link = f"{url}#{node_link_id}"
        
        node_id = f"{node_parent}{node_level_classifier}={node_number}/"
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
       
         ### INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        
        new_level_container = element.find_element(By.CLASS_NAME, "toc-branch")
        scrape_level(new_level_container, url, top_level_title, node_id)
        wait = WebDriverWait(DRIVER, 10)
        section_close_container = element.find_element(By.CLASS_NAME, "toc-heading-2").find_element(By.CLASS_NAME, "toc-parent-indicator")
        click_with_wait_and_retry(section_close_container)
        reset_page()
        


       

        


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "nm/",
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
        "nm/statutes/",
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
        "nm/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)
    
    




    



def click_with_wait_and_retry(element, max_retries=3):
    DRIVER.execute_script("arguments[0].scrollIntoView();", element)
    wait = WebDriverWait(DRIVER, 10)
    retries = 0

    while retries < max_retries:
        try:
            element_clicker = wait.until(EC.element_to_be_clickable(element))
            element_clicker.click()
            break
        except Exception as e:
            print(f"Failed to click element. Error: {e}")
            retries += 1
            if retries == max_retries:
                raise

def click_and_get_containers(element, data_anchor_text, max_retries=3):

    
    
    wait = WebDriverWait(DRIVER, 10)
    retries = 0

    while retries < max_retries:
        try:
            DRIVER.execute_script("arguments[0].scrollIntoView();", element)
            element_clicker = wait.until(EC.element_to_be_clickable(element))
            element_clicker.click()
            section_a_link = DRIVER.find_element(By.ID, f"{data_anchor_text}")
            _a = section_a_link.tag_name
            
            return section_a_link
        except Exception as e:
            print(f"Failed to click element w tag names. Error: {e}")
            retries += 1
            if retries == max_retries:
                raise

def check_tag_name_with_retry(element, tag_name, max_retries=3):
    retries = 0

    while retries < max_retries:
        try:
            if element.tag_name == tag_name:
                return True
            else:
                return False
        except Exception as e:
            print(f"Failed to check tag name. Error: {e}")
            retries += 1
            if retries == max_retries:
                raise

def find_element_XPATH_with_retry(element, x_path,  max_retries=3):
    retries = 0
    

    while retries < max_retries:
        try:
            # Store the result of find_element in a temporary variable
            next_element = element.find_element(By.XPATH, x_path)
            
            # Try to access a property to check if the next_sibling is stale
            _ = next_element.tag_name
            
            return next_element
        except Exception as e:
            print(f"Failed to find next sibling. Error: {e}")
            retries += 1
            if retries == max_retries:
                raise

def get_all_children_soup(section_a_link, mode="text"):
    text_iterator = find_element_XPATH_with_retry(section_a_link, "..")
    
    


    text_iterator_parent = find_element_XPATH_with_retry(text_iterator, "..")
    if text_iterator_parent.get_attribute("class").strip() == "":
        print("NO CLASS CASE!")
        text_iterator = text_iterator_parent
        
        text_iterator_parent = find_element_XPATH_with_retry(text_iterator, "..")

    text_iterator_soup = BeautifulSoup(text_iterator.get_attribute("outerHTML"), features="html.parser")
    text_iterator_parent_soup = BeautifulSoup(text_iterator_parent.get_attribute("outerHTML"), features="xml")
    

    all_children_soup = text_iterator_parent_soup.find_all(recursive=False)
    for i, child in enumerate(all_children_soup):
        print(i)
    print(len(all_children_soup))
    print(text_iterator_parent_soup.prettify())
    exit(1)

    while True:
        if len(all_children_soup) == 0:
            break

        print(all_children_soup[0].prettify())
        if all_children_soup[0] is text_iterator_soup:
            exit_bool = True
            break
        exit_bool = False
        
        
        index = 0
        for i, child in enumerate(all_children_soup[0].find_all(recursive=False)):
            # print(child.attrs)
            if child is text_iterator_soup:
                exit_bool = True
                index = i
                break
            
                

        if exit_bool:      
            return all_children_soup[0][index+1:].extend(all_children_soup[1:])
        else:
            all_children_soup.pop(0)

    
    return all_children_soup

if __name__ == "__main__":
    main()