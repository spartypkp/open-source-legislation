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
import utils.utilityFunctions as util

# Define the type of exception you want to retry on.
# In this case, we are retrying on URLError which can be thrown by urllib.request.urlopen
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://law.lis.virginia.gov"
TABLE_NAME = "va_node"
    
# Go to the chapter index and get all links 
def read_all_top_level_titles():
    url = "https://law.lis.virginia.gov/vacode/"

    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    toc_div = soup.find("dl", class_="number-descrip-list")

    if toc_div:
        chapter_items = toc_div.find_all("dt", recursive=False)

        for chapter_item in chapter_items:
            a_tag = chapter_item.find("a")
            chapter_link = a_tag['href']

        with open(f"{DIR}/top_level_titles.txt", "w") as write_file:
            for link in chapter_link:
                output_link = BASE_URL + link['href'] + "\n"
                write_file.write(output_link)
        write_file.close()

read_all_top_level_titles()


# #CREATE TABLE TABLE_NAME (
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



