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
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

BASE_URL  = "https://www.faa.gov/"
TOC_URL = "https://www.faa.gov/air_traffic/publications/atpubs/aim_html/"
 = "will"
TABLE_NAME = "aim_node"

# https://www.faa.gov/air_traffic/publications/atpubs/aim_html/
# https://www.faa.gov/air_traffic/publications/atpubs/aim_html/chap_1.html
# https://www.faa.gov/air_traffic/publications/atpubs/aim_html/chap1_section_1.html

def main():
    scrape_definitions()
    #scrape_abbreviations()
    exit(1)
    try:
        insert_jurisdiction_and_corpus_node()
    except psycopg2.errors.UniqueViolation as e:
        print(e)
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < 2:
                continue
            
            if i % 2 == 0:
                top_level_title = line.strip()
            else:
                link = line.strip()
                scrape_for_title(top_level_title, link)
    


def scrape_for_title(top_level_title, link):
    print(link)
    response = urllib.request.urlopen(link)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    page_container = soup.find(class_="navigation-container-main")
    header_container = page_container.find(class_="nav-menu")
    
    h1 = header_container.find("h1").get_text().strip()
    
    chapter_number = h1.split(" ")[1]
    chapter_number = chapter_number.replace(".", "")
    top_level_title = chapter_number
    chapter_name = h1
    chapter_node_id = f"us/aim/CHAPTER={chapter_number}/"
    node_type = "structure"
    chapter_data = (chapter_node_id, top_level_title, node_type, "chapter", None, None, None, link, None, chapter_name, None, None, None, None, None, "us/aim/", None, None, None, None, None)
    insert_node(chapter_data)
    
    
    section_container = soup.find(class_="nav-list book-chapter")
    
    for section in section_container.find_all(recursive=False):
        
        section_link_element = section.find("a")
        #print(section_link_element['href'])
        temp = section_link_element['href'].replace(".html", "")
        section_number = temp.split("_")[-1]
        section_link = TOC_URL + section_link_element['href'].replace("./", "/")
        print(section_link)
        node_type = "structure"
        section_text = None
        section_citation = None
        section_name = f"Section {section_number}. {section_link_element.get_text().strip()}"
        section_node_id = f"{chapter_node_id}SECTION={section_number}/" 
        node_tags = None
        section_data = (section_node_id, top_level_title, node_type, "section", section_text, None, section_citation, section_link, None, section_name, None, None, None, None, None, chapter_node_id, None, None, None, None, node_tags)
        insert_node(section_data)
        scrape_pages(section_node_id, section_link, top_level_title)

def scrape_pages(section_node_id, section_link, top_level_title):
    response = urllib.request.urlopen(section_link)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    all_pages = soup.find(class_="list-style-type-decimal")
    node_type = "content"
    node_level_classifier = "page"
    
    for page in all_pages.find_all(recursive=False):
        print(page.strong.get_text())
        node_name = None    
        node_number = page.find("a")['id'].replace("$paragraph", "")
        print(node_number)
        #print(node_number)
        node_citation = f"AIM {node_number}"
        node_id = f"{section_node_id}PAGE={node_number}"
        
        all_links = page.find_all("a", recursive=True)
        all_links_text = []
        for link in all_links:
            try:
                if link['id'] != None:
                    continue
            except:
                continue
            
            temp = link['href'].strip()
            if(temp[0] == "#"):
                continue
            all_links_text.append(temp)


        node_references = json.dumps({"links": all_links_text})
        node_text = []
        for i, element in enumerate(page.find_all(recursive=False)):
            if i == 0:
                continue
            if i == 1:
                node_name = element.get_text().strip()
            else:
                for j, li in enumerate(element.find_all(recursive=False)):
                    node_text.append(li.get_text().strip())
        
        page_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, section_link, None, node_name, None, None, None, None, None, section_node_id, None, None, node_references, None, None)
        insert_node(page_data)



def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "us/",
        None,
        "jurisdiction",
        "FEDERAL",
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
        "us/aim/",
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
        "mhl/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)


def scrape_abbreviations():
    link = "https://www.faa.gov/air_traffic/publications/atpubs/aim_html/appendix_3.html"
    node_parent = "us/aim/"
    response = urllib.request.urlopen(link)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    soup = soup.find(class_="faa_table")
    table = soup.tbody
    abbreviations = {}
    final = {"abbreviations": abbreviations}
    print("Here!")
    # app_data = ("us/aim/APPENDIX=3/", None, "structure", "appendix", None, None, None, link, None, "Abbreviations/Acronyms", None, None, None, None, None, "us/aim/", None, None, None, None, None)
    # insert_node(app_data)
    for i, tr in enumerate(table.find_all(recursive=False)):
        if i == 0:
            continue
        all_shit = []
        for child in tr.children:
            all_shit.append(child.get_text().strip().replace("\n", ""))
        
        term = all_shit[1]
        meaning = all_shit[-1]
        abbreviations[term] = meaning
        node_text = [f"The abbreviation {term} has the meaning: {meaning}"]
    abb_data = (f"us/aim/APPENDIX=3/ABBREVIATION=ALL", None, "abbreviation_dict", "abbreviation_dict", None, None, None, link, None, None, None, None, None, None, None, "us/aim/APPENDIX=3/", None, None, None, None, json.dumps(final))
    insert_node(abb_data)
        

def scrape_definitions():
    alphabet = "abcdefghijklnmopqrstuvw"
    for ch in alphabet:
        url = f"https://www.faa.gov/air_traffic/publications/atpubs/pcg_html/glossary-{ch}.html"
        node_id = f"us/aim/GLOSSARY={ch}/"
        data = (node_id, None, "structure", "structure", None, None, None, url, None, f"Glossary for {ch}", None, None, None, None, None, "us/aim/", None, None, None, None, None)
        insert_node_ignore_duplicate(data)
        scrape_individual_definition(url, node_id)

def scrape_individual_definition(url, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    main_container = soup.find(id="main")
    all_definitions = {}
    for i, ul in enumerate(main_container.find_all(class_="paragraph-title")):
        text=ul.get_text().strip()
        split_text = text.split("-")
        definition = split_text.pop().strip()
        term = "-".join(split_text).strip()
        all_definitions[term] = definition
        node_text = [f"{term} means {definition}"]
        abb_data = (f"{node_parent}DEFINITION={i}", None, "definition", "definition",node_text , None, None, url, None, None, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node(abb_data)
    final = {"definitions": all_definitions}
    abb_data = (f"{node_parent}DEFINITION=ALL", None, "definition_toc", "definition_toc",None , None, None, url, None, None, None, None, None, None, None, node_parent, None, None, None, None, json.dumps(final))
    insert_node(abb_data)

        






    



if __name__ == "__main__":
    main()