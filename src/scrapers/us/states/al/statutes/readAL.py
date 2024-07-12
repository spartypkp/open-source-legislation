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
BASE_URL = "https://alisondb.legislature.state.al.us/alison/codeofalabama/1975/"
TABLE_NAME = "al_node"
    
# Go to the chapter index and get all links 
def read_all_top_level_titles():
    url = "https://alisondb.legislature.state.al.us/alison/codeofalabama/1975/title.htm"

    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode('utf-8')
        print("URL Content Fetched")  # Debugging print

        soup = BeautifulSoup(text, 'html.parser')
        title_div = soup.find("body")
        print("Body Tag Found:", title_div is not None)  # Debugging print

        if title_div:
            title_items = title_div.find_all("p", recursive=False)
            print("Paragraph Tags Found:", len(title_items))  # Debugging print

            title_links = []

            for title_item in title_items:
                a_tag = title_item.find("a")
                if a_tag and 'href' in a_tag.attrs:
                    full_link = BASE_URL + a_tag['href']
                    title_links.append(full_link)
                    print("Found link:", full_link)  # Debug print

            with open(f"{DIR}/data/top_level_titles.txt", "w") as write_file:
                for link in title_links:
                    write_file.write(link + "\n")
            print(f"Links written to file: {len(title_links)}")

        else:
            print("No body tag found in the HTML.")

    except Exception as e:
        print("An error occurred:", e)

read_all_top_level_titles()



# CREATE TABLE TABLE_NAME (
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



