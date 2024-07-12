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


DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://law.lis.virginia.gov"
TABLE_NAME = "va_node"
 = "madeline"
SKIP_TITLE = 0

def main():
    insert_jurisdiction_and_corpus_node()
    
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file):
            if i < SKIP_TITLE:
                continue
            url = line
            if ("title" in url):
                top_level_title = url.split("title")[-1].strip()
                top_level_title = top_level_title.replace("/", "")
            else:
                continue    
            scrape_per_title(url, top_level_title, "va/statutes/")



# Scrapes all nodes for a given top level title. Provide the url and the name
# https://www.flsenate.gov/Laws/Statutes/2023/Title1/#Title1
def scrape_per_title(url, top_level_title, node_parent):

    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    title_container = soup.find("span", id="va_code")
    title_name_get = title_container.find("h2")
    title_name = title_name_get.get_text()
    title_node_number = top_level_title
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"{node_parent}TITLE={title_node_number}/"
    title_node_parent = node_id
    node_link = url
    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, title_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_containers = title_name_get.find_next_siblings()
    for next_container in next_containers:
        if next_container and next_container.name == 'dl':
            if ("TITLE=58.1" in title_node_parent):
                chapters = next_container.find("dt")
                a_tag = chapters.find("a")
                node_link = BASE_URL + a_tag['href']
                scrape_per_chapter_58(node_link, top_level_title, title_node_parent)
            else:
                chapters = next_container.find_all("dt")
                for chapter in chapters:
                    a_tag = chapter.find("a")
                    node_link = BASE_URL + a_tag['href']
                    if ("Chapter" in a_tag.get_text()):
                        scrape_per_chapter(node_link, top_level_title, title_node_parent)
                    else:
                        scrape_per_section(node_link, top_level_title, title_node_parent)
              

        elif next_container and next_container.name == 'ul':
            subtitles = next_container.find("span", id=lambda x: x and x.startswith("subtitle"))
            if subtitles:
                subtitle_name = subtitles.get_text()
                subtitle_node_number = subtitle_name.split(" ")[1].replace(".", "")
                node_type = "structure"
                node_level_classifier = "SUBTITLE"
                node_id = f"{title_node_parent}SUBTITLE={subtitle_node_number}/"
                node_parent = title_node_parent
                subtitle_parent = node_id
                node_link = url
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, subtitle_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                insert_node(node_data)

                next_level_part = next_container.find_all("ul")
                if next_level_part:
                    for level in next_level_part:
                        next_level_type = level.find("b")
                        if next_level_type:
                            next_level_type = next_level_type.get_text()
                            if ("Part" in next_level_type):
                                part_name = next_level_type
                                part_node_number = next_level_type.split(" ")[1].replace(".", "")
                                node_type = "structure"
                                node_level_classifier = "PART"
                                node_id = f"{subtitle_parent}PART={part_node_number}/"
                                part_node_parent = node_id
                                node_parent = subtitle_parent
                                node_link = url
                                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                                insert_node(node_data)
                                sections_or_chapters = level.find_all("dt")
                                for section in sections_or_chapters:
                                    a_tag = section.find("a")
                                    type_check = a_tag.get_text()
                                    if ("Chapter" in type_check):
                                        node_link = BASE_URL + a_tag['href']
                                        scrape_per_chapter(node_link, top_level_title, part_node_parent)
                                    else:
                                        node_link = BASE_URL + a_tag['href']
                                        scrape_per_part_section(node_link, top_level_title, part_node_parent)
                        else:        
                            chapters = level.find_all("dt")
                            for chapter in chapters:
                                a_tag = chapter.find("a")
                                node_link = BASE_URL + a_tag['href']
                                scrape_per_chapter(node_link, top_level_title, subtitle_parent)
                        
                else:        
                    chapters = level.find_all("dt")
                    for chapter in chapters:
                        a_tag = chapter.find("a")
                        node_link = BASE_URL + a_tag['href']
                        scrape_per_chapter(node_link, top_level_title, title_node_parent)
            else:
                parts_container = next_container.find("span", id=lambda x: x and x.startswith("part"))
                if parts_container:
                 
                    part_name = parts_container.get_text()
                    part_node_number = part_name.split(" ")[1].replace(".", "")
                    node_type = "structure"
                    node_level_classifier = "PART"
                    node_id = f"{title_node_parent}PART={part_node_number}/"
                    node_parent = title_node_parent
                    part_node_parent = node_id
                    node_link = url
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    insert_node(node_data)

                    parts_container = next_container.find_all("dt")
                
                    for part in parts_container:
                        a_tag = part.find("a")
                        sections_check = a_tag.get_text()
                        if ("Part" in sections_check):
                            node_link = BASE_URL + a_tag['href']
                            scrape_per_part_section(node_link, top_level_title, part_node_parent, "NONE")
                        elif("Sections" in sections_check):
                            node_link = BASE_URL + a_tag['href']
                            scrape_per_part_section(node_link, top_level_title, part_node_parent, "PART")
                            break
                        else:
                            a_tag = part.find("a")
                            node_link = BASE_URL + a_tag['href']
                            scrape_per_chapter(node_link, top_level_title, title_node_parent)
                    



def scrape_per_chapter(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text)
    print(url)

    chapter_container = soup.find("span", id="va_code")
    chapter_name_get = chapter_container.find("h2")
    texts = []

    for content in chapter_name_get.contents:
    # Check if content is not an <a> tag and is not a string containing only whitespace
        if content.name != 'a' and content.string and content.string.strip():
            texts.append(content.string.strip())

# Join all the pieces of text into one string
    chapter_name = " ".join(texts)
    print(chapter_name)
    chapter_node_number = chapter_name.split()[1].strip('.')
    print(chapter_node_number)

    if ("Repealed" in chapter_name):
        node_type = "reserved"
        node_level_classifier = "CHAPTER"
        node_id = f"{node_parent}CHAPTER={chapter_node_number}/"
        next_node_parent = node_id
        node_link = url
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        return
    else:
        node_type = "structure"
        node_level_classifier = "CHAPTER"
        node_id = f"{node_parent}CHAPTER={chapter_node_number}/"
        next_node_parent = node_id
        node_link = url
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        
    next_containers = chapter_name_get.find_next_siblings()
    for next_container in next_containers:
    # print(next_container)
        if next_container and next_container.name == 'dl':
            sections = next_container.find_all("dt")
            for section in sections:
                a_tag = section.find("a")
                node_link = BASE_URL + a_tag['href']
                scrape_per_section(node_link, top_level_title, next_node_parent)
        elif next_container and next_container.name == 'ul':
            print(next_container)
            articles = next_container.find("span", id=lambda x: x and x.startswith("article"))
            article_name = articles.get_text()
            article_node_number = article_name.split()[1].rstrip('.')
            node_type = "structure"
            node_level_classifier = "ARTICLE"
            node_id = f"{next_node_parent}ARTICLE={article_node_number}/"
            node_parent = next_node_parent
            article_node_parent = node_id
            node_link = url
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, article_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node(node_data)

            dt_tags = next_container.find_all("dt")
            for dt_tag in dt_tags:
                a_tag = dt_tag.find("a")
                node_link = BASE_URL + a_tag['href']
                scrape_per_section(node_link, top_level_title, article_node_parent)
                
                 
def scrape_per_chapter_58(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text)

    chapter_container = soup.find("span", id="va_code")
    chapter_name_get = chapter_container.find("h2")
    chapter_name = chapter_name_get.get_text()
    chapter_node_number = "0"
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_id = f"{node_parent}CHAPTER={chapter_node_number}/"
    next_node_parent = node_id
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_containers = chapter_name_get.find_next_siblings()
    for next_container in next_containers:
        if next_container and next_container.name == 'dl':
            sections = next_container.find_all("dt")
            for section in sections:
                a_tag = section.find("a")
                node_link = BASE_URL + a_tag['href']
                scrape_per_section(node_link, top_level_title, next_node_parent)
        elif next_container and next_container.name == 'ul':
            print(next_container)
            articles = next_container.find("span", id=lambda x: x and x.startswith("article"))
            article_name = articles.get_text()
            article_node_number = article_name.split()[1].rstrip('.')
            node_type = "structure"
            node_level_classifier = "ARTICLE"
            node_id = f"{next_node_parent}ARTICLE={article_node_number}/"
            node_parent = next_node_parent
            article_node_parent = node_id
            node_link = url
            node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, article_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node(node_data)

            dt_tags = next_container.find_all("dt")
            for dt_tag in dt_tags:
                a_tag = dt_tag.find("a")
                node_link = BASE_URL +  a_tag['href']      
                scrape_per_section(node_link, top_level_title, article_node_parent)   




def scrape_per_part_section(url, top_level_title, node_parent, part_check):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text)

    part_container = soup.find("span", id="va_code")
    if part_check == "PART":
        sections = part_container.find_all("dt")
        for section in sections:
            a_tag = section.find("a")
            node_link = BASE_URL + a_tag['href']
            scrape_per_section(node_link, top_level_title, node_parent)
        return

    part_name = part_container.find("h2").get_text()
    part_node_number = part_name.split(" ")[2].replace(".", "")
    node_type = "structure"
    node_level_classifier = "PART"
    node_id = f"{node_parent}PART={part_node_number}/"
    next_node_parent = node_id
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, part_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    sections = part_container.find_all("dt")
    for section in sections:
        a_tag = section.find("a")
        node_link = BASE_URL + a_tag['href']
        scrape_per_section(node_link, top_level_title, next_node_parent)




def scrape_per_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`;
    soup = BeautifulSoup(text)

    section_container = soup.find("span", id="va_code")
    first_child = section_container.find_all()[0]
    node_tags = {'HistoryNote': [], 'SideNote': []}
    if first_child.name == 'p':
        node_tags['SideNote'] = first_child.get_text()
        
    section_name_get = section_container.find("h2")
    section_name = section_name_get.get_text()
    if ("Repealed" in section_name or "Expired" in section_name or "Reserved" in section_name):
        section_number_split = section_name.split(" ")
        number_part_with_extra = section_number_split[2].split('-')
        section_node_number = number_part_with_extra[1].rstrip(',')
        node_type = "reserved"
        node_level_classifier = "SECTION"
        node_id = f"{node_parent}SECTION={section_node_number}"
        node_link = url
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, section_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node(node_data)
        return
    section_number_split = section_name.split(" ")
    print(section_number_split)
    number_part_with_extra = section_number_split[2].split('-')
    print(number_part_with_extra)
    section_node_number = number_part_with_extra[1].rstrip('.')
    print(section_node_number)
    node_type = "content"
    node_level_classifier = "SECTION"
    node_id = f"{node_parent}SECTION={section_node_number}"
    node_text = []
    node_references = {'internal': [], 'external': []}
    node_addendum = None

    node_text_container = section_name_get.find_next_sibling()
    section_text = node_text_container.find_all("p")
    if len(section_text) < 1:
        pass
    else:
        last_p = section_text[-1]
    for section in section_text:
        internal_references = section.find_all("a")
        if internal_references and section != last_p:
            for internal_reference in internal_references:
                internal_text = internal_reference.get_text()
                node_references['internal'].append(f"§{internal_text}")
        paragraph_text = section.get_text()
        if section == last_p:
            node_addendum = paragraph_text
        else:
            paragraph_text = paragraph_text.encode('ascii', 'ignore').decode('ascii')
            node_text.append(paragraph_text)

    node_history = soup.find("div", id="HistoryNote")
    if node_history:
        node_tags['HistoryNote'] = node_history.get_text()
    node_tags = json.dumps(node_tags)  # Convert dictionary to JSON string
    node_references = json.dumps(node_references) 
    # node_text = json.dumps(node_text)  # Convert list to JSON string

    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, None, node_link, node_addendum, section_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
    insert_node_ignore_duplicate(node_data)

    







    

    



# THIS FUNCTION SHOULD ONLY BE RAN ONCE PER SCRAPE
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "va/",
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
        "va/statutes/",
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
        "va/",
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