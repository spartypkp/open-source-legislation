import os
import sys
# BeautifulSoup imports
from bs4 import BeautifulSoup
from bs4.element import Tag

# Selenium imports
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from typing import List, Tuple
import time
import json
import re

from pathlib import Path

DIR = os.path.dirname(os.path.realpath(__file__))
# Get the current file's directory
current_file = Path(__file__).resolve()

# Find the 'src' directory
src_directory = current_file.parent
while src_directory.name != 'src' and src_directory.parent != src_directory:
    src_directory = src_directory.parent

# Get the parent directory of 'src'
project_root = src_directory.parent

# Add the project root to sys.path
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils.pydanticModels import NodeID, Node, Addendum, AddendumType, NodeText, Paragraph, ReferenceHub, Reference, DefinitionHub, Definition, IncorporatedTerms, ALLOWED_LEVELS
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup



SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "ks"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"

BASE_URL = "https://www.kslegislature.org"
TOC_URL = "https://www.kslegislature.org/li/b2023_24/statute/"


def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape_toc_page(corpus_node)

def scrape_toc_page(node_parent: Node):
    soup = get_url_as_soup(TOC_URL)

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for tr in all_trs[64:]:
        link = tr.find("a")
        
        chapter_url = TOC_URL + link['href']
        if ("chapter" in chapter_url):
            b_tag = tr.find("b")
            node_name = b_tag.get_text().strip()
            number = node_name.split()
            if number[-1] == ".":
                number = number[:-1]
            top_level_title = number

            parent = node_parent.node_id
            level_classifier = "chapter"
            node_id = f"{parent}/chapter={top_level_title}" 

            node_type = "structure"
            status = None
            link = chapter_url

            chapter_node = Node(
                id=node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=top_level_title,
                parent=parent,
                status=status
            )
            insert_node(chapter_node, TABLE_NAME, debug_mode=True)
            
            scrape_articles(chapter_node)

# Chapter -> Article -> Section
def scrape_articles(node_parent: Node):
    chapter_url = str(node_parent.link)
    soup = get_url_as_soup(chapter_url)

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for tr in all_trs: 
        link = tr.find("a")
        
        article_url =  chapter_url + link['href']
        
        if ("article" in article_url):
            b_tag = tr.find("b")
            node_name = b_tag.get_text().strip()
            number = node_name.split()
            number = number[1].replace('.', '')
            if number[-1] == ".":
                number = number[:-1]
            level_classifier = "article"
            parent = node_parent.node_id
            node_id = f"{parent}/{level_classifier}={number}" 
            node_type = "structure"
            
            link = article_url
            status = None
            article_node = Node(
                id=node_id,
                link=link,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=node_parent.top_level_title,
                parent=parent,
                status=status
            )
            insert_node(article_node, TABLE_NAME, debug_mode=True)
            scrape_sections(article_node)

def scrape_sections(node_parent: Node):
    article_url = str(node_parent.link)
    soup = get_url_as_soup(article_url)
    
    #href="../../001_000_0000_chapter/001_002_0000_article/001_002_0001_section/001_002_0001_k/"

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for i, tr in enumerate(all_trs): 
        link = tr.find("a")
        section_url_get = link['href'] 
        cleaned_url = section_url_get.replace('../../', '')
        section_url = TOC_URL+ cleaned_url
        
        top_level_title = node_parent.top_level_title
        parent = node_parent.node_id
        

        section_soup = get_url_as_soup(section_url)
        soup_statutefull = section_soup.find("div", id="statutefull")
        all_tables = soup_statutefull.find_all("table")
        

        node_type = "content"
        level_classifier = "section"
        link = section_url
        core_metadata = None 
        
        addendum = Addendum()
    
        text_table = all_tables[1]
            

        node_text = NodeText()
        paragraph = text_table.find("td")
    
        
    
        number_span = paragraph.find_all("span", class_="stat_5f_number")
        number = ""
        for element in number_span:
            number += element.get_text().strip()
        
            # number2 = number.split("-")[-1].replace('.','')
            print(number)
        number2 = number.split("-")[-1].replace('.','')
        print(number2)
        node_caption_span = paragraph.find("span", class_="stat_5f_caption")
        if node_caption_span is None:
            node_name = "BLANK"
        else:
            node_name_add = node_caption_span.get_text().strip()
            node_name = f"Section {number2} {node_name_add}"
        node_id = f"{node_parent}SECTION={number2}" 
        citation = f"KS Stat § {number2}"

        for element in paragraph.find_all(recursive=False):
            text = element.get_text().strip()
            node_text.add_paragraph(text=text)


            
                
        addendum_table = all_tables[2]
        paragraph = addendum_table.find("p")

        if paragraph is None:
            addendum = None
        else:
            addendum.history = AddendumType(text=paragraph.get_text().strip())
                

        status = None
        
        section_node = Node(
            id=node_id,
            link=link,
            citation=citation,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            node_text=node_text,
            addendum=addendum,
            top_level_title=top_level_title,
            parent=parent,
            status=status
        )
        
        
        insert_node(section_node, TABLE_NAME, debug_mode=True)
    


if __name__ == "__main__":
     main() 