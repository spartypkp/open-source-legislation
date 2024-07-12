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
import utils.utilityFunctions as util
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "http://webserver.rilin.state.ri.us/Statutes/"
TABLE_NAME = "ri_node"
 = "madeline"

def main():
    # insert_jurisdiction_and_corpus_node()
    
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file, start=1):  # Start enumeration from 1
            if i < 23:
                continue 
            url = line
            if ("TITLE" in url):
                top_level_title = url.split("TITLE")[-1].strip()
                top_level_title = top_level_title.rsplit('/', 1)[0]
            else:
                continue
    
            scrape_per_title(url, top_level_title, "ri/statutes/")

def scrape_per_title(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find("body")
    title_tag = soup.find("h1")
    node_name = title_tag.get_text().strip()
    formatted_node_name = re.sub(r"(\d)([A-Z][a-z])", r"\1 \2", node_name)
    node_number = top_level_title
    node_type = "structure"
    node_level_classifier = "TITLE"
    node_id = f"{node_parent}TITLE={node_number}/"
    node_link = url
    title_node_parent = node_id

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, formatted_node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    chapter_links = soup.find_all("p")
    modified_url = url.rsplit('/', 1)[0]

    for chapter in chapter_links:
        a_tag = chapter.find("a")
        chapter_url = modified_url + "/" + a_tag["href"] 
        print("this is chapter url:" + chapter_url)
        node_parent = title_node_parent
        scrape_per_chapter(chapter_url, top_level_title, node_parent)

def scrape_per_chapter(url, top_level_title, node_parent):
    response = make_request(url)
    if response is None:
        return
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find("body")
    chapter_title_tag = soup.find("h2")
    for i, child in enumerate(chapter_title_tag.center.children):
            if i == 0:
                node_number = child.text.strip()
                print(node_number)
            if i == 2: 
                node_name_add = child.text

    node_number_add = node_number.split(" ")[-1]
    node_name = f"{node_number} {node_name_add}"
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    node_id = f"{node_parent}CHAPTER={node_number_add}/"
    node_link = url
    chapter_node_parent = node_id

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_links = soup.find_all("p")
    modified_url = url.rsplit('/', 1)[0]

    if next_links is None:
        print("blank chapter")
        page_contents = soup.find("h2")
        chapter_check = page_contents.get_text().strip()
        if ("Chapter " in chapter_check):
            pass


    for link in next_links:
        part_check = link.get_text()
        if part_check.startswith("Part"):
            a_tag = link.find("a")
            url = modified_url + "/" + a_tag["href"] 
            part_node_parent = chapter_node_parent
            scrape_per_part(url, top_level_title, part_node_parent)
        elif part_check.startswith("Article"):
            a_tag = link.find("a")
            url = modified_url + "/" + a_tag["href"] 
            article_node_parent = chapter_node_parent
            scrape_per_article(url, top_level_title, article_node_parent)
        else:
            a_tag = link.find("a")

            if a_tag is None:
                print("a_tag is None. Unable to find <a> tag within the link.")
                continue
            else:
                print(f"a_tag found: {a_tag}")
            url = modified_url + "/" + a_tag["href"] 
            node_parent = chapter_node_parent
            scrape_per_section(url, top_level_title, node_parent)
    
def scrape_per_part(url, top_level_title, node_parent):
    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text) 

    if ("/ARTICLE=" in node_parent):
        soup = soup.find("body")
        part_title_tag = soup.find("h4")
        for i, child in enumerate(part_title_tag.center.children):
            if i == 0:
                node_number = child.text.strip()
                print(node_number)
            if i == 2: 
                node_name_add = child.text
        node_number_add = node_number.split(" ")[-1]
        node_name = f"{node_number} {node_name_add}"
        node_number = node_number_add
        node_type = "structure"
        node_level_classifier = "PART"
        node_id = f"{node_parent}PART={node_number}/"
        node_link = url
        part_node_parent = node_id
    
    else:
        soup = soup.find("body")
        part_title_tag = soup.find("h3")
        for i, child in enumerate(part_title_tag.center.children):
            if i == 0:
                node_number = child.text.strip()
                print(node_number)
            if i == 2: 
                node_name_add = child.text
        node_number_add = node_number.split(" ")[-1]
        node_name = f"{node_number} {node_name_add}"
        node_number = node_number_add
        node_type = "structure"
        node_level_classifier = "PART"
        node_id = f"{node_parent}PART={node_number}/"
        node_link = url
        part_node_parent = node_id

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, part_node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_links = soup.find_all("p")
    modified_url = url.rsplit('/', 1)[0]

    for link in next_links:
        part_check = link.get_text()
        if ("Subpart " in part_check):
            a_tag = link.find("a")
            url = modified_url + "/" + a_tag["href"] 
            subpart_node_parent = part_node_parent
            scrape_per_subpart(url, top_level_title, subpart_node_parent)
        else:
            a_tag = link.find("a")
            section_url = modified_url + "/" + a_tag["href"] 
            node_parent = part_node_parent
            top_level_title = top_level_title
            scrape_per_section(section_url, top_level_title, node_parent)

def scrape_per_article(url, top_level_title, node_parent):
    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text) 

    soup = soup.find("body")
    article_title_tag = soup.find("h3")
    node_name = article_title_tag.get_text()
    formatted_node_name = re.sub(r"(\d)([A-Z])", r"\1 \2", node_name)
    node_number_add = formatted_node_name.split()
    node_number = node_number_add[1]
    node_type = "structure"
    node_level_classifier = "ARTICLE"
    node_id = f"{node_parent}ARTICLE={node_number}/"
    node_link = url
    article_node_parent = node_id

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, formatted_node_name, None, None, None, None, None, article_node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_links = soup.find_all("p")
    modified_url = url.rsplit('/', 1)[0]

    for link in next_links:
        part_check = link.get_text()
        if part_check.startswith("Part"):
            a_tag = link.find("a")
            url = modified_url + "/" + a_tag["href"] 
            part_node_parent = article_node_parent
            scrape_per_part(url, top_level_title, part_node_parent)
        else:
            a_tag = link.find("a")
            if a_tag is None:
                print("a_tag is None. Unable to find <a> tag within the link.")
                continue
            else:
                print(f"a_tag found: {a_tag}")
            url = modified_url + "/" + a_tag["href"] 
            node_parent = article_node_parent
            scrape_per_section(url, top_level_title, node_parent)


def scrape_per_subpart(url, top_level_title, node_parent):
    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text) 

    soup = soup.find("body")
    part_title_tag = soup.find("h4")
    node_name = part_title_tag.get_text()
    for i, child in enumerate(part_title_tag.center.children):
            if i == 0:
                node_number = child.text.strip()
                print(node_number)
            if i == 2: 
                node_name_add = child.text
    node_number_add = node_number.split(" ")[-1]
    node_name = f"{node_number} {node_name_add}"
    node_number = node_number_add
    node_type = "structure"
    node_level_classifier = "SUBPART"
    node_id = f"{node_parent}SUBPART={node_number}/"
    node_link = url
    subpart_node_parent = node_id

    node_text = None
    node_citation = None
    node_addendum = None
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, subpart_node_parent, None, None, None, None, None)
    insert_node(node_data)

    next_links = soup.find_all("p")
    modified_url = url.rsplit('/', 1)[0]

    for link in next_links:
        a_tag = link.find("a")
        section_url = modified_url + "/" + a_tag["href"] 
        node_parent = subpart_node_parent
        top_level_title = top_level_title
        scrape_per_section(section_url, top_level_title, node_parent)




def scrape_per_section(url, top_level_title, node_parent):
    response = make_request(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text) 
    # soup = soup.find("body")
    # section_container = soup.find_all("div")
    node_type = "content"
    node_level_classifier = "SECTION"
    node_link = url
    node_text = []

    body = soup.find("body")
    if ("/PART=" in node_parent or "/ARTICLE=" in node_parent):
        if("/SUBPART=" in node_parent and "/PART=" in node_parent):
            last_div = body.find_all("div")[4]
            print(last_div)
        elif("/ARTICLE=" in node_parent and "/PART=" in node_parent):
            last_div = body.find_all("div")[4]
            print(last_div)
        elif("/ARTICLE=" in node_parent and "/SUBPART=" in node_parent):
            last_div = body.find_all("div")[4]
            print(last_div)
        else:
            last_div = body.find_all("div")[3]
    
    else:
        last_div = body.find_all("div")[2]

    node_name = None
    node_number = None
    citation_number = None
    node_text = []
    node_addendum = None
 
    first_p = last_div.find("p")
    print(first_p)
    node_name = first_p.get_text().strip()
    citation_number1 = node_name.split()[1]
    citation_number = citation_number1.rstrip('.')
    node_number = citation_number.split("-")[-1]
    print(citation_number)

    for p_tag in first_p.find_next_siblings("p"):
        node_text.append(p_tag.get_text().strip())

    all_divs = body.find_all("div")
    if all_divs:
        node_addendum = all_divs[-1].get_text().strip()
        # node_addendum = node_addendum.
    else:
        node_addendum = ""

    node_id = f"{node_parent}SECTION={node_number}"
    node_citation = f"RI Gen L § {citation_number} (2022)"
    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node(node_data)

    # text_section = section_container[2]
    # # print(section_container)
    # # print(text_section)
    # text_sections_paragraphs = text_section.find_all("p")
    # # print(text_sections_paragraphs)

    # last_element = text_sections_paragraphs[-1]
    # node_number = None
    # whole_section_number = None
    # node_addendum = None

    # print(text_section)

    # for element in text_section.find_all(recursive=False):
    #     if element == 0:
    #         node_name_get = element.find("b")
    #         print(node_name_get)
    #         if node_name_get:
    #             node_name = node_name_get.get_text().strip()
    #             node_number_get = node_name.split()
    #             whole_section_number = node_number_get[1]
    #             node_number_add = node_number_get[1].split("-")
    #             node_number = node_number_add[-1]
    #     elif element != last_element:
    #         node_text_get = element.get_text().strip
    #         node_text = node_text.append(node_text_get)
    #     elif element == last_element:
    #         node_addendum = last_element.get_text().strip()

    
        # node_id = f"{node_parent}SECTION={node_number}"
        # node_citation = f"RI Gen L § {whole_section_number} (2022)"
        # node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        # insert_node(node_data)


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ri/",
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
        "ri/statutes/",
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
        "ri/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)





# @retry(
#     retry=retry_if_exception_type(URLError),       # Retry on URLError
#     wait=wait_exponential(multiplier=1, max=60),   # Exponential backoff with a max wait of 60 seconds
#     stop=stop_after_attempt(5)                     # Stop after 5 attempts
# )
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