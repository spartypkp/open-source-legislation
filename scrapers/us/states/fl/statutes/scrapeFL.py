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
import sys
import psycopg2
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

# Define the type of exception you want to retry on.
# In this case, we are retrying on URLError which can be thrown by urllib.request.urlopen
from urllib.error import URLError


BASE_URL = "https://www.flsenate.gov"
TABLE_NAME = "fl_node"
 = "madeline"

def main():
    insert_jurisdiction_and_corpus_node()
    
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file):
            url = line
            if ("Title" in url):
                top_level_title = url.split("Title")[-1].strip()
            else:
                continue
    
            scrape_per_title(url, top_level_title, "fl/statutes/")

# CREATE TABLE fl_node (
#     node_order SERIAL,
#     node_id text PRIMARY KEY,
#     node_top_level_title text,
#     node_type text,
#     node_level_classifier text,
#     node_text text[],                             
#     node_text_embedding vector(1536),
#     node_citation text,
#     node_link text,
#     node_addendum text,
#     node_name text,
#     node_name_embedding vector(1536),
#     node_summary text,
#     node_summary_embedding vector(1536),
#     node_hyde text[],
#     node_hyde_embedding vector(1536),
#     node_parent text,
#     node_direct_children text[],
#     node_siblings text[],
#     node_references jsonb,
#     node_incoming_references jsonb,
#     node_tags jsonb
# );



# Scrapes all nodes for a given top level title. Provide the url and the name
# https://www.flsenate.gov/Laws/Statutes/2023/Title1/#Title1
def scrape_per_title(url, top_level_title, node_parent):


    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    # Find title, and add it as a node
    # <li>
    #   <a TITLE LINK
    #       <span id="Title1"
    #       <span class="descript"
    #       <span class="chapterRange"
    #   < ol class="chapter"
    

    # How do we extract title?
    # 1. Find the span id= Title# element
    # 2. The above <a> tag is the title_container
    # 3. Iterate over the title container
     # - Get first part of node_name: "Title I"
     # - Get second part of node_name: "CONSTRUCTION OF STATUTES"
     # - Get extra data (node_tags): {chapterRange: "(Ch. 1-2)"
    # 4. Move on to get the chapter container

    # top_level_title = 1
    # title_name: Title I
    title_span = soup.find(id=f"Title{top_level_title}")
    title_name = title_span.get_text()
    title_container = title_span.parent
    title_description = title_container.find("span", class_="descript")
    title_name += " - " + title_description.get_text()
    # title_name: Title I - CONSTRUCTION OF STATUTES

    chap_range = title_container.find("span", class_="chapterRange").get_text()
    node_tags = {}
    node_tags['chap_range'] = chap_range
    node_tags = json.dumps(node_tags)
    # add the title as a node
    node_type = "structure"
    node_level_classifier = "TITLE"
    # fl/statutes/
    node_id = f"{node_parent}TITLE={top_level_title}/" 
    node_name = title_name
    
    # Figure out node link
    node_link = url
    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
    insert_node(node_data)
    
    chapters_ol = title_container.parent.find("ol", class_="chapter")
        
    chapter_items = chapters_ol.find_all("li", recursive=False)

    for chapter_item in chapter_items:
        a_tag = chapter_item.find("a")
        chapter_link = a_tag['href']

        expanded_url = BASE_URL + chapter_link + "/All"
        print(expanded_url)
        
        # Handle the chapter here, then feed in the "expandedChapter to scrape"
        
        scrape(expanded_url, top_level_title, node_id)


# First url: https://www.flsenate.gov/Laws/Statutes/2023/Chapter1
def scrape(url, top_level_title, node_parent):
    
    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')
    
    # logic for content node section 

    # To go into a section class=CatchlineIndex
    # For every IndexItem find 'a' and then section index is href


    
    # Chapter nodes
    # Part nodes
    # Section nodes

    chapter_container = soup.find("div", class_="Chapter")

    
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_link = url

    chap_num = chapter_container.find("div", class_="ChapterNumber")
    chapter_number = chap_num.get_text().split(" ")[-1]
    chapter_node_id = f"{node_parent}CHAPTER={chapter_number}/"


    chap_name = chapter_container.find("div", class_="ChapterName")
    chapter_name = chap_name.get_text().strip()
    node_name = "Chapter " + chapter_number + " - " + chapter_name

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (chapter_node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)
    node_parent = chapter_node_id

    all_parts = chapter_container.find_all(class_="Part")
    print(all_parts is None or len(all_parts) == 0)
    if all_parts is None or len(all_parts) == 0:
        all_section_divs = chapter_container.find_all(class_="Section")

        for i, section in enumerate(all_section_divs):
            node_type = "content"
            node_level_classifier = "SECTION"
            node_link = url
            

            node_text = []
            # Make a citation
            
            node_addendum = None

            section_number = section.find(class_="SectionNumber").get_text().strip()
            node_citation = f"Fla. Stat. § {section_number}"
            node_name = "Section " + section_number + " - "

            section_name = section.find(class_="Catchline")
            section_name_add = section_name.get_text().strip()
            node_name += section_name_add

            section_text = section.find(class_="SectionBody")
            # Need to loop over every html element in sectionBody
            for i, element in enumerate(section_text.find_all(recursive=False)):
                current_text = element.get_text().strip()
                node_text.append(current_text)

            history = section.find(class_="History")
            node_addendum = history.get_text().strip()
            
            node_tags = None
            if section.find(class_="Note") is not None:
                node_tags = {}
                note = section.find(class_="Note").get_text().strip()
                node_tags['note'] = note
                node_tags = json.dumps(node_tags)
            
            
            node_id = f"{node_parent}SECTION={section_number}"
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
            insert_node(node_data)
            
    else:
        for i, part in enumerate(all_parts):

            node_type = "structure"
            node_level_classifier = "PART"
            node_link = url

            
            part_number = part.find("div", class_="PartNumber").get_text()
            part_number = part_number.split(" ")[-1]
            part_node_id = f"{node_parent}PART={part_number}/"


            part_name = part.find("span", class_="PartTitle")
            part_name_add = part_name.get_text()
            node_name = "Part " + part_number + " - " + part_name_add

            node_text = None
            node_citation = None
            node_addendum = None
            node_data = (part_node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node(node_data)

            
            all_section_divs = part.find_all(class_="Section")

            for i, section in enumerate(all_section_divs):
                node_type = "content"
                node_level_classifier = "SECTION"
                node_link = url
                section_node_parent = part_node_id

                node_text = []
                # Make a citation
                node_citation = None
                node_addendum = None


                section_num = section.find(class_="SectionNumber")
                section_number = section_num.get_text().strip()
                node_name = "Section " + section_number + " - "

                section_name = section.find(class_="Catchline")
                section_name_add = section_name.get_text().strip()
                node_name += section_name_add

                section_text = section.find(class_="SectionBody")
                
                # Need to loop over every html element in sectionBody
                for i, element in enumerate(section_text.find_all(recursive=False)):
                    current_text = element.get_text().strip()
                    node_text.append(current_text)

                history = section.find(class_="History")
                node_addendum = history.get_text().strip()
                
                node_tags = None
                if section.find(class_="Note") is not None:
                    node_tags = {}
                    note = section.find(class_="Note").get_text().strip()
                    node_tags['note'] = note
                    node_tags = json.dumps(node_tags)
                

                node_id = f"{section_node_parent}SECTION={section_number}"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, section_node_parent, None, None, None, None, node_tags)
                insert_node(node_data)



    

                # add chapter as a structure node
                # call scrape_per_title recursively
                # url is chapter_link 
                # node_parent needs to be recenetly added chapter node id



# THIS FUNCTION SHOULD ONLY BE RAN ONCE PER SCRAPE
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "fl/",
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
        "fl/statutes/",
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
        "fl/",
        None,
        None,
        None,
        None,
        None,
    )
    try:
        util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    except psycopg2.errors.UniqueViolation as e:
        print(e)
    try:
        util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)
    except psycopg2.errors.UniqueViolation as e:
        print(e)
    return





# Decorator to implement exponential backoff retry strategy
@retry(
    retry=retry_if_exception_type(URLError),       # Retry on URLError
    wait=wait_exponential(multiplier=1, max=60),   # Exponential backoff with a max wait of 60 seconds
    stop=stop_after_attempt(5)                     # Stop after 5 attempts
)
def make_request(url):
    # This will try to open the URL. If it fails with URLError, it will retry.
    response = urllib.request.urlopen(url)
    return response





    

if __name__ == "__main__":
     main() 