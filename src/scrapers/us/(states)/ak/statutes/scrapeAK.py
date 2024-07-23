
import os
from bs4 import BeautifulSoup


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

import time
from bs4.element import Tag
import sys
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

from src.utils.pydanticModels import NodeID, Node, Addendum, AddendumType, NodeText, Paragraph, ReferenceHub, Reference, DefinitionHub, Definition, IncorporatedTerms
from src.utils.scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, selenium_element_present, selenium_elements_present



COUNTRY = "us"
# State code for states, 'federal' otherwise
JURISDICTION = "ak"
# 'statutes' is current default
CORPUS = "statutes"
# No need to change this
TABLE_NAME =  f"{COUNTRY}_{JURISDICTION}_{CORPUS}"


# The base URL of the corpus's official .gov website
BASE_URL = "https://www.akleg.gov"
# The URL of the Table of Contents
TOC_URL = "https://www.akleg.gov/basis/statutes.asp"
# Start scraping at a specific top_level_title
SKIP_TITLE = 2 # 0/47 titles
RESERVED_KEYWORDS = {"[Repealed": "repealed", "[Renumbered": "renumbered"}

# === Jurisdiction Specific Global Variables ===
# Selenium Driver
DRIVER = None



def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(country_code=COUNTRY, jurisdiction_code=JURISDICTION, corpus_code=CORPUS)
    scrape_all_titles(corpus_node)

def scrape_all_titles(corpus_node: Node):
    global DRIVER
    # Use Selenium in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    DRIVER = webdriver.Chrome(options=chrome_options)
    # In case visual debugging needed
    # DRIVER = webdriver.Chrome()

    DRIVER.get(TOC_URL)

    toc_nav_container =  WebDriverWait(DRIVER, 5).until(selenium_element_present(DRIVER, (By.ID, "TOC_A")))
    toc_nav_container.click()

    for i in range(SKIP_TITLE, 47):
        titles_container = WebDriverWait(DRIVER, 5).until(selenium_element_present(DRIVER, (By.ID, "TitleToc")))
        all_titles = WebDriverWait(DRIVER, 20).until(selenium_elements_present(titles_container, (By.TAG_NAME, "li")))

        title_container = all_titles[i]

        title_a_tag = title_container.find_element(By.TAG_NAME, "a")

        title_name = title_a_tag.text.strip()
        
        top_level_title = title_name.split(" ")[1]

        if top_level_title[-1] == ".":
            top_level_title = top_level_title[:-1]
        
        # I want to convert top level title to a string with leading zeros ex: 1 -> 01, 21 -> 21
        citation = top_level_title.zfill(2)
        link = TOC_URL + "#" + citation
        node_type = "structure"
        level_classifier = "title"
        title_node_id = f"{corpus_node.node_id}/{level_classifier}={top_level_title}"
        
        ### Get title information, Add title node
        title_node = Node(
            id=title_node_id,
            top_level_title=top_level_title,
            number=top_level_title,
            node_type=node_type,
            node_name=title_name,
            level_classifier=level_classifier,
            citation="AS " + citation,
            link=link,
            parent=corpus_node.node_id
        )
        
        insert_node(node=title_node, table_name=TABLE_NAME, ignore_duplicate=True, debug_mode=True)
        title_a_tag.click()
        

        scrape_all_chapters(title_node)
        title_return = DRIVER.find_element(By.ID, "titleLink")
        title_return.click()
        

def scrape_all_chapters(node_parent: Node):
    
    chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
    try:
        all_chapters = WebDriverWait(DRIVER, 20).until(selenium_elements_present(chapters_container, (By.XPATH, ".//a[contains(@href, 'javascript:void(0)')]")))
    # Title has no chapters (See Title 7)
    except:
        return

    for i in range(len(all_chapters)):
        # Find ChapterToc and all_chapters again, prevent StaleElementReferenceException
        if i > 0:
            chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
            all_chapters = WebDriverWait(DRIVER, 20).until(selenium_elements_present(chapters_container, (By.XPATH, ".//a[contains(@href, 'javascript:void(0)')]")))

        chapter_container= all_chapters[i]
        chapter_a_soup = BeautifulSoup(chapter_container.get_attribute("outerHTML"), features="html.parser")

        chapter_name = chapter_a_soup.get_text()
        chapter_number = chapter_name.split(" ")[1]

        if chapter_number[-1] == ".":
            chapter_number = chapter_number[:-1]
        
        node_type = "structure"
        level_classifier = "chapter"
        citation =  node_parent.citation + "." + chapter_number
        chapter_number = str(int(chapter_number))
        link = TOC_URL + "#" + citation

        status=None
        for word, new_status in RESERVED_KEYWORDS.items():
            if word in chapter_name:      
                status = new_status
                break

        node_id = f"{node_parent.node_id}/{level_classifier}={chapter_number}"
        chapter_node = Node(
            id=node_id,
            top_level_title=node_parent.top_level_title,
            node_type=node_type,
            number=chapter_number,
            node_name=chapter_name,
            level_classifier=level_classifier,
            citation=citation,
            link=link,
            parent=node_parent.node_id,
            status=status
        )
        
        insert_node(node=chapter_node, table_name=TABLE_NAME, debug_mode=True)
        # If chapter is not reserved
        if not status:
            chapter_container.click()
            try:
                scrape_all_sections(chapter_node)
            except:
                print("** FAILED SCRAPING SECTIONS! RETRYING!")
                scrape_all_sections(chapter_node)
            chapter_return = DRIVER.find_element(By.ID, "partHead").find_element(By.TAG_NAME, "a")
            chapter_return.click()
            

        
        
def scrape_all_sections( node_parent: Node):
    # ".//a[contains(@href, 'statutes.asp?year=2023')]"
    sections_container = DRIVER.find_element(By.ID, "ChapterToc")
    try:
        all_sections =  WebDriverWait(DRIVER, 20).until(selenium_elements_present(sections_container, (By.XPATH, ".//a[contains(@href, 'statutes.asp?')]")))
    # Indicates a case where a chapter has NO sections
    except:
        return
    current_article = ""
    
    for i, section_element in enumerate(all_sections):

        section_container = BeautifulSoup(section_element.get_attribute("outerHTML"), features="html.parser")

        node_name = section_container.get_text().strip()
        number = node_name.split(" ")[1]
        
        if number[-1] == ".":
            number = number[:-1]
        
        section_citation = number
        node_type = "content"
        level_classifier = "section"
        link = TOC_URL + "#" + section_citation
        node_text=None
        core_metadata = None
        processing = None
        addendum=None
        incoming_references=None

       
        
        status=None
        for word, new_status in RESERVED_KEYWORDS.items():
            if word in node_name:      
                status = new_status
                break
        
        # Don't process reserved section text/addendumn
        if not status:  
            #Example section link:  https://www.akleg.gov/basis/statutes.asp#02.15.010
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            section_driver = webdriver.Chrome(options=chrome_options)
            section_driver.get(link)
            
            # sideSection is always present, however content is dynamically loaded
            sidebar_section_container = section_driver.find_element(By.ID, "sideSection")
            # Wait until side section content loads (Can take up to 10 seconds, sometimes fails) 
            # We wont actually use this, just need it as indicator for page load
            sidebar_section_content = WebDriverWait(section_driver, 20).until(selenium_element_present(sidebar_section_container, (By.TAG_NAME, "div")))      
            # Get the main section content as Beautiful Soup Element         
            section_soup = BeautifulSoup(section_driver.page_source, features="html.parser").body
            all_text_container = section_soup.find(id="content")
            
            text_container = all_text_container.find("a", attrs={"name": section_citation})
            iterator = text_container.parent

            # Find parent article, if exists
            for tag in iterator.previous_elements:
                if not isinstance(tag, Tag):
                    continue
                
                if tag.find("h7") is not None:
                    article_container = tag.find("h7")
                    article_name = article_container.get_text().strip()
                    article_number = article_name.split(" ")[1]

                    if article_number[-1] == ".":
                        article_number = article_number[:-1]
                    article_node_type = "structure"
                    
                    

                    article_node_id = f"{node_parent.node_id}/article={article_number}"
                    article_node = Node(
                        id=article_node_id,
                        top_level_title=node_parent.top_level_title,
                        number=article_number,
                        node_type=article_node_type,
                        node_name=article_name,
                        level_classifier="article",
                        citation=f"{node_parent.citation} Article {article_number}",
                        link=link,
                        parent=node_parent.node_id,
                        status=status
                    )
                    # Articles can be repeated many times for children sections, ignore duplicates during insert
                    insert_node(article_node, table_name=TABLE_NAME, ignore_duplicate=True, debug_mode=True)
                    
                    current_article=f"/article={article_number}"
                    break

            
            node_text = NodeText()
            
            # This is so dirty, and I apologize for this shit
            # Scrape main section content
            while True:
                reference_hub = None
                # Use beautifulSoup iterator
                iterator = iterator.next_sibling
                if iterator is None:
                    break
                # If the element is a BS4 Tag
                if isinstance(tag, Tag):
                    # Skip bold
                    if iterator.name == "b":
                        break
                    
                    # Get the text, remove whitespace, check if tag is anchor tag
                    txt = iterator.get_text().strip()
                    if iterator.name == "a":
                        if reference_hub is None:
                            reference_hub = ReferenceHub()
                        href = iterator["href"]
                        # Indicates a same-site (same corpus) reference, corpus is None
                        if "#" in href:
                            hashtag_index = href.index("#")
                            
                            href_clean = href[hashtag_index+1:]
                           
                            href_split = href_clean.split(".")
                           
                            main_constructed_node_id = f"us/ak/statutes"
                            # Iterate and construct the reference ID
                            for i, href_number in enumerate(href_split):
                                if i == 0:
                                    main_constructed_node_id += f"/title={str(int(href_number))}"
                                elif i == 1:
                                    main_constructed_node_id += f"/chapter={str(int(href_number))}"
                                else:
                                    main_constructed_node_id += f"/section={href_clean}"
                                
                            if processing is None:
                                processing = {}

                            processing["node_text"] = "Check Article existince, update reference id"
                            
                            ref_link = "https://www.akleg.gov/basis/" + href
                            reference = Reference(text=txt, placeholder=None, id=main_constructed_node_id)
                            reference_hub.references[ref_link] = reference
                        # Indicates an external site (different corpus) reference, set corpus to other
                        # TODO: Experiment for common outgoing corpus tags and incorporate logic here
                        else:
                            reference = Reference(text=txt, placeholder=None, corpus="other")
                            reference_hub.references[href] = reference
                            
                    if txt == "":
                        continue
                    node_text.add_paragraph(text=txt, reference_hub=reference_hub)
                else:
                    txt = iterator
                    #print(txt)
                    if txt == "":
                        continue
            # Process the addendum container
            addendum_soup = BeautifulSoup(section_driver.page_source, features='html.parser')
            addendum_container = addendum_soup.find(id="sideSection").find("div")
            addendum = Addendum()
            incoming_references = None
            
            
            core_metadata = {}
            
            if addendum_container is not None:
                
                category = None
                last_reference_link = ""
                
                for i, element in enumerate(addendum_container.contents):
                    
                    if isinstance(element, Tag):
                        # Skip <br>
                        if element.name == "br":
                            continue

                        txt = element.get_text()
                        # Heading indicates new category
                        if element.name == "h5":
                            
                            category = txt.lower()
                            if category != "history" and category != "references" and category not in core_metadata:
                                core_metadata[category] = {"node_text": NodeText()}
                            else:
                                addendum.history = AddendumType(type="history", text="")

                            continue
                        # Handle references within sidebar content, possibly addendum references
                        if element.name == "a":
                            href = element["href"].replace(" ", "")
                            tag_link = "https://www.akleg.gov/basis/" + href

                            reference = Reference(text=txt)
                            
                            
                            if category == "history":
                                if addendum.history.reference_hub is None:
                                    addendum.history.reference_hub = ReferenceHub()
                                addendum.history.reference_hub.references[tag_link] = reference
                            elif category == "references":
                                if incoming_references is None:
                                    incoming_references = ReferenceHub()
                                incoming_citation = reference.text.split(" ")[-1]
                                incoming_citation_split = incoming_citation.strip().split(".")
                                # CHECK FOR PARENT ARTICLE LATER, ADDING TO PROCESSING

                                constructed_node_id = f"us/ak/statutes/title={incoming_citation_split[0]}/chapter={str(int(incoming_citation_split[1]))}/section={incoming_citation.strip()}"
                                if processing is None:
                                    processing = {}

                                processing["incoming_references"] = "Check Article existince, update reference id"
                                reference.id = constructed_node_id
                                incoming_references.references[tag_link] = reference

                            else:
                                if 'reference_hub' not in core_metadata[category]:
                                    core_metadata[category]['reference_hub'] = ReferenceHub()
                                
                                node_text_category: NodeText = core_metadata[category]['node_text']
                                node_text_category.add_paragraph(text=txt)

                                reference_hub_category: ReferenceHub = core_metadata[category]['reference_hub']
                                reference_hub_category.references[tag_link] = reference
                                
                                core_metadata[category]['reference_hub'] = reference_hub_category
                                core_metadata[category]['node_text'] = node_text_category

                            
                            last_reference_link = tag_link

                    # Handle regular text, not BS4 Tags
                    else:
                        txt = element
                        if txt == "":
                            continue
                        # Add text to the history addendum
                        if category == "history":
                            if addendum.history.text != "":

                                addendum.history.text += f"\n{txt}"
                            else:
                                addendum.history.text += txt
                        # Add text to the last incoming_reference
                        elif category == "references":
                            incoming_references.references[last_reference_link].text += f"\n{txt}"
                        else:
                            node_text_category: NodeText = core_metadata[category]['node_text']
                            node_text_category.add_paragraph(text=txt)
                            core_metadata[category]['node_text'] = node_text_category     

        # Correctly set section parent to article, if an article was found
        section_node_id = f"{node_parent.node_id}{current_article}/{level_classifier}={number}"
        parent= f"{node_parent.node_id}{current_article}"
        # Otherwise set section parent to chapter
       

        # Don't pollute rows with empty dictionaries
        if core_metadata == {}:
            core_metadata=None
        
        section_node = Node(
            id=section_node_id, 
            top_level_title=node_parent.top_level_title, 
            node_type=node_type, 
            number=number, 
            node_name=node_name, 
            level_classifier=level_classifier, 
            node_text=node_text, 
            citation="AS " + section_citation, 
            link=link, 
            status=status,
            addendum=addendum, 
            parent=parent, 
            core_metadata=core_metadata,
            incoming_references=incoming_references,
            processing=processing
        )
        
        insert_node(section_node, TABLE_NAME, debug_mode=True)
        

if __name__ == "__main__":
    main()