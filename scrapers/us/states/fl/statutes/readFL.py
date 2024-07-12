from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

# Define the type of exception you want to retry on.
# In this case, we are retrying on URLError which can be thrown by urllib.request.urlopen
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://www.flsenate.gov"
TABLE_NAME = "fl_node"

def main():
    with open(f"{DIR}/top_level_titles.txt") as text_file:
        for i, line in enumerate(text_file):
            url = line
            if ("Title" in url):
                top_level_title = url.split("Title")[-1].strip()
            else:
                continue
        
            
    
            scrape_per_title(url, top_level_title, "fl/statutes/", ())
    
    
# Go to the chapter index and get all links 
def read_all_top_level_titles():
    url = "https://www.flsenate.gov/Laws/Statutes/2023"

    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    toc_div = soup.find("div", class_="statutesTOC")

    if toc_div:
        chapters_ol = toc_div.find("ol", class_="chapter")
        
        if chapters_ol:
            chapter_items = chapters_ol.find_all("li", recursive=False)

            for chapter_item in chapter_items:
                a_tag = chapter_item.find("a")
                chapter_link = a_tag['href']

        with open(f"{DIR}/top_level_titles.txt", "w") as write_file:
            for link in all_links:
                output_link = BASE_URL + link['href'] + "\n"
                write_file.write(output_link)
        write_file.close()
    
    else:
        print("The element with id 'statutesTOC' was not found in the HTML.")


# CREATE TABLE fl_node (
#     node_order SERIAL,
#     node_id text PRIMARY KEY,
#     node_top_level_title text,
#     node_type text,
#     node_level_classifier text,
#     node_text text[],                             
#     node_text_embedding text,
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
#     node_references json,
#     node_incoming_references json,
#     node_tags json
# );



