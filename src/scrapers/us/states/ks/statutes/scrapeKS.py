from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import sys
import psycopg2
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://www.kslegislature.org/li/b2023_24/statute/"
TABLE_NAME = "ks_node"
 = "madeline"

def main():
    # insert_jurisdiction_and_corpus_node()

    URL = "https://www.kslegislature.org/li/b2023_24/statute/"
   
    response = urllib.request.urlopen(URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for tr in all_trs[64:]:
        link = tr.find("a")
        
        chapter_url = BASE_URL + link['href']
        if ("chapter" in chapter_url):
            b_tag = tr.find("b")
            node_name = b_tag.get_text().strip()
            node_number = node_name.split()
            top_level_title = node_number[1].replace('.', '')

            node_parent = "ks/statutes/"
            node_level_classifier = "CHAPTER"
            node_id = f"{node_parent}CHAPTER={top_level_title}/" 

            node_type = "structure"
            node_text = None
            node_link = chapter_url
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node(node_data)
            node_parent = node_id
            scrape_per_title(chapter_url, top_level_title, node_parent)

# Chapter -> Article -> Section
def scrape_per_title(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)
   

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for tr in all_trs: 
        link = tr.find("a")
        
        article_url = url + link['href']
        
        if ("article" in article_url):
            b_tag = tr.find("b")
            node_name = b_tag.get_text().strip()
            node_number = node_name.split()
            article_number = node_number[1].replace('.', '')
            node_level_classifier = "ARTICLE"
            node_id = f"{node_parent}ARTICLE={article_number}/" 
            node_type = "structure"
            node_text = None
            node_link = article_url
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node(node_data)
            article_node_parent = node_id
            scrape_per_article(article_url, top_level_title, article_node_parent)

def scrape_per_article(url, top_level_title, node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)
    
    #href="../../001_000_0000_chapter/001_002_0000_article/001_002_0001_section/001_002_0001_k/"

    soup = soup.find(id="statutefull")
    soup2 = soup.find("center")
    all_trs = soup2.find_all("tr")

    for i, tr in enumerate(all_trs): 
        link = tr.find("a")
        section_url_get = link['href'] 
        cleaned_url = section_url_get.replace('../../', '')
        section_url = BASE_URL+ cleaned_url
        print("new section url:" + section_url)
        top_level_title = top_level_title
        section_node_parent = node_parent
        
        scrape_per_section(section_url, top_level_title, section_node_parent)

def scrape_per_section(url, top_level_title, section_node_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    soup_statutefull = soup.find("div", id="statutefull")
    all_tables = soup_statutefull.find_all("table")
    
 

    node_type = "content"
    node_level_classifier = "SECTION"
    node_link = url
    top_level_title = top_level_title  
    node_tags = None 
    node_parent = section_node_parent
    node_addendum = None
   

    
    text_table = all_tables[1]
        

    node_text = []
    paragraph = text_table.find("td")
 
    
   
    node_number_span = paragraph.find_all("span", class_="stat_5f_number")
    node_number = ""
    for element in node_number_span:
        node_number += element.get_text().strip()
      
        # node_number2 = node_number.split("-")[-1].replace('.','')
        print(node_number)
    node_number2 = node_number.split("-")[-1].replace('.','')
    print(node_number2)
    node_caption_span = paragraph.find("span", class_="stat_5f_caption")
    if node_caption_span is None:
        node_name = "BLANK"
    else:
        node_name_add = node_caption_span.get_text().strip()
        node_name = f"Section {node_number2} {node_name_add}"
    node_id = f"{node_parent}SECTION={node_number2}" 
    node_citation = f"KS Stat § {node_number2}"

    for element in paragraph.find_all(recursive=False):
        node_text.append(element.get_text())


           
            
    addendum_table = all_tables[2]
    
    paragraph = addendum_table.find("p")

    if paragraph is None:
        pass

    else:
        node_addendum = paragraph.get_text().strip()
            

    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)  
    insert_node(node_data)
    
       


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ks/",
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
        "ks/statutes/",
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
        "ks/",
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