import os
import sys
# BeautifulSoup imports
from bs4 import BeautifulSoup
from bs4.element import Tag


from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains

from typing import List, Tuple
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, get_url_as_soup, selenium_element_present, selenium_elements_present



SKIP_TITLE = 0 # If you want to skip the first n titles, set this to n
COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "tx"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"


BASE_URL = "https://statutes.capitol.texas.gov"
TOC_URL = "https://statutes.capitol.texas.gov/Index.aspx"
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
DRIVER = None

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    # scrape_constitution
    scrape_all_codes(corpus_node)



def scrape_all_codes(node_parent: Node):
    
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    

    # Get the container of all titles
    codes_container =  WebDriverWait(DRIVER, 5).until(selenium_element_present(DRIVER, (By.ID, "ctl00_ContentPlaceHolder1_NavTreet1")))
    codes_container.click()
    
    parent = node_parent.node_id
    for i in range(SKIP_TITLE, 31):
        
        codes_container =  WebDriverWait(DRIVER, 5).until(selenium_element_present(DRIVER, (By.ID, "ctl00_ContentPlaceHolder1_NavTreen1Nodes")))
        # code_container =  WebDriverWait(DRIVER, 5).until(selenium_elements_present(codes_container, (By.TAG_NAME, "table")))


        soup = BeautifulSoup(DRIVER.page_source, features="html.parser").body
        title_soup = soup.find(id="ctl00_ContentPlaceHolder1_NavTreen1Nodes")
        title_table = title_soup.find_all("table", recursive=False)[i]
        #print(title_table.prettify())

        name_container = title_table.tbody.tr.find_all("td", recursive=False)[-1]
        node_name = name_container.get_text().strip()
        level_classifier = "code"
       

        top_level_title = CODE_MAP[node_name].lower()
        number = top_level_title
        node_type = "structure"
        link = TOC_URL
        node_id = f"{parent}/{level_classifier}={top_level_title}"
        status=None
        code_node = Node(
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
        insert_node(code_node, TABLE_NAME, debug_mode=True)
        

        a_tag = name_container.find("a")
        title_table_id = a_tag.get("id").replace("Treet", "Treen") + "Nodes"
        print(title_table_id)
        
        title_table_selenium = DRIVER.find_element(By.ID, a_tag.get("id"))
        # ctl00_ContentPlaceHolder1_NavTreet2
        # Scroll to the title table
        DRIVER.execute_script("arguments[0].scrollIntoView();", title_table_selenium)
        title_table_selenium.click()

        title_table_selenium = DRIVER.find_element(By.ID, a_tag.get("id"))
        temp = WebDriverWait(DRIVER, 5).until(selenium_element_present(DRIVER, (By.ID, title_table_id)))
        # ctl00_ContentPlaceHolder1_NavTreen1Nodes
        

        # Get the title table one last time, tree HTML loaded
        soup = BeautifulSoup(DRIVER.page_source, features="html.parser").body      
        level_container = soup.find(id=f"{title_table_id}")
        if level_container.find_all(recursive=False)[0].find(class_="PDFicon") is not None:
            scrape_sections(node_parent, level_container)
        else:
            scrape_level(node_parent, level_container)


        DRIVER = webdriver.Chrome()
        DRIVER.get(TOC_URL)
        # Get the container of all titles
        titles_container = DRIVER.find_element(By.ID, "ctl00_ContentPlaceHolder1_NavTree")
        titles_table = titles_container.find_elements(By.TAG_NAME, "table")[1]

        # Open the titles table
        titles_table.click()
        

        
    

def scrape_level(node_parent: Node, level_container: Tag):
    
    all_child_containers = level_container.find_all(recursive=False)
    for i in range(0, len(all_child_containers), 2):
        
        current_level = all_child_containers[i]
        node_name = current_level.get_text().strip()
        level_classifier = node_name.split(" ")[0].lower()
        number = node_name.split(" ")[1]
        if number[-1] == ".":
            number = number[:-1]
        node_type = "structure"
        link = TOC_URL
        parent = node_parent.node_id
        node_id = f"{parent}/{level_classifier}={number}"
        status = None
        try:
            next_level_container = all_child_containers[i+1]
        except:
            status = "reserved"
        

         ## INSERT STRUCTURE NODE, if it's already there, skip it
        structure_node = Node(
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
        insert_node(structure_node, TABLE_NAME, debug_mode=True)
        
        
        if status is None:
            if next_level_container.find_all(recursive=False)[0].find(class_="PDFicon") is not None:
                scrape_sections(structure_node, next_level_container)
            else:
                scrape_level(structure_node, next_level_container)





def scrape_sections(node_parent: Node, level_container: Tag):
    
    for i, child in enumerate(level_container.find_all(recursive=False)):
        
        all_a_tags = child.find_all("a")
        #print(len(all_a_tags))
        name_tag = all_a_tags[1]
        #print(name_tag.prettify())
        node_name = name_tag.get_text().strip()
        level_classifier = node_name.split(" ")[0]
        number = node_name.split(" ")[1]
        if number[-1] == ".":
            number = number[:-1]
        node_type = "structure"
        link_tag = all_a_tags[3]
        link = link_tag.get("href")

        status = None
        chapter_node_id = f"{node_parent}/{level_classifier}={number}"
        chapter_node = Node(
            id=chapter_node_id,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            number=number,
            node_name=node_name,
            top_level_title=node_parent.top_level_title,
            parent=node_parent.node_id,
            status=status
        )
        insert_node(chapter_node, TABLE_NAME, debug_mode=True)

        
        file_target = link.split("/")[-1]
        directory_target = file_target.split(".")[0] + ".htm"

        file_path = f"{DIR}/data/{directory_target}/{file_target}"
        
        with open(file_path, "r") as file:
            section_soup = BeautifulSoup(file.read(), features="html.parser")
            

            all_p_tags_raw = section_soup.find_all("p")
            all_p_tags = []
            # Remove all tags that have class="center"
            for p in all_p_tags_raw:
                if p.get("class") is not None:
                    if p.get("class") == []:
                        all_p_tags.append(p)
                        continue
                    if p.get("class")[0] != "center":
                        all_p_tags.append(p)

            node_id = None

            for p in all_p_tags:
                
                txt = re.sub(r'\s+', ' ', p.get_text().strip())
                if txt == "":
                    continue
                

                if txt[0:5] == "Sec. " or txt[0:5] == "Art. ":
                    print("== New Section or Article ==")
                    if node_id is not None:
                        print("== Inserting Previous Section ==")
                        section_link = link + f"#{number}"
                         ### FOR ADDING A CONTENT NODE, allowing duplicates
                        status=None
                        for word in RESERVED_KEYWORDS:
                            if word in node_name:
                                status = "reserved"
                                break
                        new_node = Node(
                            id=node_id,
                            link=section_link,
                            citation=node_citation,
                            node_type=node_type,
                            level_classifier=level_classifier,
                            number=number,
                            node_name=node_name,
                            top_level_title=node_parent.top_level_title,
                            parent=node_parent.node_id,
                            status=status
                        )
                        insert_node(new_node, TABLE_NAME, debug_mode=True)
                
                        core_metadata = {}
                        processing = {}
                        
                    # Find the index of the 4th occurence of "." in txt
                    # This is the index of the end of the section number
                    number = txt.split(" ")[1]
                    index = number.count(".") + 1
                    try:
                        node_name_index = [pos for pos, char in enumerate(txt) if char == '.'][index]
                    except:
                        node_name_index = len(txt) - 1
                    node_name = txt[0: node_name_index + 1]
                    
                    if number[-1] == ".":
                        number = number[:-1]
                    
                    full_name = ""
                    for k,v in CODE_MAP.items():
                        if v == node_parent.top_level_title:
                            full_name = k
                            break

                    # Convert full_name, which is in all caps, to camel case (TEST STRING -> Test String)
                    full_name = " ".join([word.capitalize() for word in full_name.split(" ")])
                    
                    node_citation =f"Tex. {full_name} § {number}"
                    node_addendum = Addendum()
                    if txt[0:5] == "Art. ":
                        level_classifier = "article"
                    else:
                        level_classifier = "section"
                    node_text = NodeText()
                    
                    references = find_references(p, processing)
                    node_text.add_paragraph(txt[node_name_index + 1:], reference_hub=references)
                    node_type = "content"
                    node_id = f"{chapter_node_id}/{level_classifier}={number}"
                    addendum_found = False
                    
                elif 'style' in p.attrs and not addendum_found:
                    print("== Style Case ==")
                    references = find_references(p, processing)
                    node_text.add_paragraph(txt, reference_hub=references)
                    
                else:
                    print("== Default, Addendum ==")
                    node_addendum.history = AddendumType(text= f"{txt}\n")
                    addendum_found = True
                    
                
                ### FOR ADDING A CONTENT NODE, allowing duplicates

            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    status = "reserved"
                    break

            section_link = link + f"#{number}"

            new_node = Node(
                id=node_id,
                link=section_link,
                citation=node_citation,
                node_text=node_text,
                addendum=node_addendum,
                node_type=node_type,
                level_classifier=level_classifier,
                number=number,
                node_name=node_name,
                top_level_title=node_parent.top_level_title,
                parent=chapter_node_id,
                status=status
            )
            

def find_references(p: Tag, processing) -> ReferenceHub:
    reference_hub = ReferenceHub
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
            reference_hub[citation_link] = Reference(text=citation_text)
            #temp = {"citation_link": citation_link, "citation_text": citation_text, "citation_number": citation_number}
            if "https://statutes.capitol.texas.gov" not in citation_link:
                processing['unknown_reference_corpus_in_node_text'] = True
    return reference_hub
    
    
if __name__ == "__main__":
    main()