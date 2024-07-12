import json
from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import re
import sys
import psycopg2
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://apps.leg.wa.gov/rcw/"
TABLE_NAME = "wa_node"
 = "madeline"


def main():
    # insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file, start=1):  # Start enumeration from 1
            if i < 69:
                continue 
            url = line
            if ("Cite" in url):
                top_level_title = url.split("=")[-1].strip()
                top_level_title = top_level_title
                scrape_per_title(url, top_level_title, "wa/statutes/")
            else:
                continue
            

def scrape_per_title(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)
    print(url)

    title_container = soup.find("div", id="contentWrapper")
    div_tags = title_container.find_all("div", recursive = False)
    print(div_tags)
    title_name_div_tag = div_tags[2]
    title_node_name = title_name_div_tag.get_text().strip()
    title_node_number = top_level_title
    format_title_node_name = f"Title {top_level_title} RCW {title_node_name}"
    title_node_number = top_level_title
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"{node_parent}TITLE={title_node_number}/"
    chapter_node_parent = node_id
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, format_title_node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    
    get_chapter_links = title_container.find("table")
    check_chapter_article = get_chapter_links.find_previous_sibling("h3").get_text()
    if "Articles" in check_chapter_article:
        article_links = get_chapter_links.find_all("tr")
        for article in article_links:
            a_tag = article.find("a")
            url = a_tag['href']
            print(url)
            scrape_per_article(url, top_level_title, chapter_node_parent)

    print(get_chapter_links)
    chapter_links = get_chapter_links.find_all("tr")

    for chapter in chapter_links:
        a_tag = chapter.find("a")
        url = a_tag['href']
        print(node_parent)
        scrape_per_chapter(url, top_level_title, chapter_node_parent)
    

def scrape_per_chapter(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)
    print(url)

    chapter_container = soup.find("div", id="contentWrapper")
    div_tags = chapter_container.find_all("div")
    chapter_number_div = div_tags[0]
    chapter_name_div = div_tags[2]
    chapter_node_name = chapter_name_div.get_text()
    chapter_node_number = chapter_number_div.find("a")
    node_number = chapter_node_number.get_text().split('.')[-1]
    node_name = f"Chapter {node_number} RCW {chapter_node_name}"
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_id = f"{node_parent}CHAPTER={node_number}/"
    section_node_parent = node_id
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    get_section_links = chapter_container.find_all("tr")

    for section in get_section_links:
        a_tag = section.find("a")
        if a_tag:
            a_tags = section.find_all("a")
            first_atag = a_tags[0]
            url = first_atag['href']
            print(url)
            top_level_title = top_level_title
            node_parent = section_node_parent
            scrape_per_section(url, top_level_title, node_parent)
        else:
            continue

def scrape_per_article(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    article_container = soup.find("div", id="contentWrapper")
    div_tags = article_container.find_all("div")
    article_number_div = div_tags[0]
    article_name_div = div_tags[2]
    article_node_name = article_name_div.get_text()
    node_number = article_number_div.get_text().split('Article ')[-1]
    node_name = f"Article {node_number} RCW {article_node_name}"
    node_type = "structure"
    node_level_classifier = "ARTICLE"
    node_id = f"{node_parent}ARTICLE={node_number}/"
    article_node_parent = node_id
    node_link = url
    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    get_section_links = article_container.find_all("tr")
    current_part = None
    part_node_parent = None

    for section in get_section_links:
        a_tag = section.find("a")
        if a_tag is None:
            check_part = section.get_text()
            if check_part.startswith('PART'):
                node_name = check_part
                node_name = re.sub(r'(\d)([A-Z])', r'\1 \2', node_name)
                print(node_name)
                node_number = node_name.split(' ')[1]
                node_sub_number = node_name.split(' ')[2].rstrip('.')
                node_id = f"{article_node_parent}PART={node_number}/"
                print(node_id)
                node_type = "structure"
                node_level_classifier = "PART"
                part_node_parent = node_id
                node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, url, None, node_name, None, None, None, None, None, article_node_parent, None, None, None, None, None)
                insert_node(node_data)
                current_part = node_number
            else:
                subpart_match = re.match(r'([A-Z])\.', check_part)
                if subpart_match and current_part:
                    node_name = f"PART {current_part} {check_part}"
                    node_number = node_name.split(' ')[1]
                    node_sub_number = node_name.split(' ')[2].rstrip('.')
                    node_id = f"{article_node_parent}PART={node_number}{node_sub_number}/"
                    print(node_id)
                    node_type = "structure"
                    node_level_classifier = "PART"
                    part_node_parent = node_id
                    node_link = url
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    insert_node(node_data)
        else:
            a_tags = section.find_all("a")
            first_atag = a_tags[0]
            url = first_atag['href']
            print(url)
            top_level_title = top_level_title
            if part_node_parent is not None:
                node_parent = part_node_parent
            else:
                node_parent = article_node_parent

            print(node_parent)
            scrape_per_section(url, top_level_title, node_parent)
            continue


def scrape_per_section(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find("div", id="contentWrapper")
    section_container = soup.get_text()
    
    
    text = re.sub(r"^PDFRCW\s*", "", section_container)
    
    node_text = []
    node_tags = []
    section_number_search = text[:20]
   

    section_number_match = re.search(r"(\d+\.\d+\.\d+)", section_number_search)
    section_number_match2 = re.search(r"(\d+\.\d+[A-Za-z]*\.\d+)", section_number_search)
    section_number_match3 = re.search(r"(\d+[A-Za-z]*\.\d+\.\d+)", section_number_search)
    section_number_match4 = re.search(r"(\d+[A-Za-z]*\.\d+[A-Za-z]*\.\d+)", section_number_search)
    section_number_match5 = re.search(r"(\d+[A-Za-z]*\.\d+-\d+)", section_number_search)
    section_number_match6 = re.search(r"(\d+[A-Za-z]*\.\d+[A-Za-z]*-\d+)", section_number_search)


    if section_number_match:
        section_number = section_number_match.group(1)
    if section_number_match2:
        section_number = section_number_match2.group(1)
    if section_number_match3:
        section_number = section_number_match3.group(1)
    if section_number_match4:
        section_number = section_number_match4.group(1)
    if section_number_match5:
        section_number = section_number_match5.group(1)
    if section_number_match6:
        section_number = section_number_match6.group(1)
    remaining_text = text.replace(section_number, '', 1).strip() if section_number else text

    node_name_match = re.match(r"([^.]+\.)(?![^\[]*\])", remaining_text)
    node_name = node_name_match.group(1).strip() if node_name_match else ""

    node_name = f"Section {section_number} RCW {node_name}"
    print(node_name)

    text = remaining_text.replace(node_name, ' ', 1).strip() if node_name else text
 
    node_addendum_match = re.search(r"\[([^\]]+)\]", text)
    node_addendum = node_addendum_match.group(1).strip() if node_addendum_match else ""

 
    text = re.sub(r"\[.*?\]", "", text).strip()

    node_tags_match = re.search(r"NOTES:(.*)", text)
    node_tags_description = node_tags_match.group(1).strip() if node_tags_match else ""
   
    text = re.sub(r"NOTES:.*", "", text).strip()
    emdash = '\u2014'
    section_text = text.strip().replace("\n", " ").replace(emdash, "-")
    formatted_section_text = re.sub(r'([.,])(?=[^\s])', r'\1 ', section_text)
    final_text = formatted_section_text.encode().decode('utf-8').replace('\"', '')
    node_text.append(final_text.strip())
    node_tags = {"notes": node_tags_description}
    node_tags = json.dumps(node_tags)
    
    node_number = section_number.split('.')[-1]
    node_type = "content"
    node_level_classifier = "SECTION"
    node_id = f"{node_parent}SECTION={node_number}"
    node_link = url
    node_citation = f"{section_number} RCW"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
    insert_node_ignore_duplicate(node_data)

def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "wa/",
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
        "wa/statutes/",
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
        "wa/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)





@retry(
    retry=retry_if_exception_type(URLError),       # Retry on URLError
    wait=wait_exponential(multiplier=1, max=60),   # Exponential backoff with a max wait of 60 seconds
    stop=stop_after_attempt(5)                     # Stop after 5 attempts
)
def make_request(url):
    try:
        # Attempt to open the URL
        response = urllib.request.urlopen(url)
        return response

    except urllib.error.HTTPError as e:
        # Check if the error is a 404 Not Found
        if e.code == 404:
            print(f"URL not found, skipped: {url}")
            return None


if __name__ == "__main__":
     main() 
    