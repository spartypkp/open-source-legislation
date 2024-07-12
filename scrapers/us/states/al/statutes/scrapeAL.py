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
from scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node, insert_node_ignore_duplicate

# Define the type of exception you want to retry on.
# In this case, we are retrying on URLError which can be thrown by urllib.request.urlopen
from urllib.error import URLError


DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://alisondb.legislature.state.al.us/alison/codeofalabama/1975/"
TABLE_NAME = "al_node"

def main():
    insert_jurisdiction_and_corpus_node()
    
    # with open(f"{DIR}/data/top_level_titles.txt") as text_file:
    #     for i, line in enumerate(text_file):
    #         url = line
    #         if ("Title" in url):
    #             top_level_title = url.split("Title")[-1].strip()
    #         else:
    #             continue
    url = "https://alisondb.legislature.state.al.us/alison/codeofalabama/1975/title.htm"
    top_level_title = None
    scrape_title(url, top_level_title, "al/statutes/")


def scrape_title(url, top_level_title, node_parent):

    url = "https://alisondb.legislature.state.al.us/alison/codeofalabama/1975/title.htm"


    response = make_request(url)
    if response is None:
        return
    data = response.read() # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    title_div = soup.find("body")
    
    # print("Body Tag Found:", title_div is not None)  # Debugging print

    if title_div:
        title_items = title_div.find_all("p", recursive=False)
        print("Paragraph Tags Found:", len(title_items))

        for i, title in enumerate(title_items):
            if i < 45:
                continue
            
            a_tag = title.find("a")
            title_number = a_tag.get_text().split(" ")[-1]
            title_name_add = a_tag.next_sibling
            title_name = title_name_add.get_text()
            top_level_title = title_number

            href_link = a_tag['href']

            node_type = "structure"
            node_level_classifier = "TITLE"
            # fl/statutes/
            node_id = f"{node_parent}TITLE={top_level_title}/" 
            node_name = f"Title {title_number} {title_name}/" 
            node_link = BASE_URL + href_link
            title_node_parent = node_id

            node_text = None
            node_citation = None
            node_addendum = None
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            insert_node_ignore_duplicate(node_data)
            print(node_link)


            scrape_next_page(node_link, top_level_title, title_node_parent)


def scrape_next_page(url, top_level_title, node_parent):
    response = make_request(url)
    if response is None:
        return
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    body_div = soup.find("body")
    p_container = body_div.find_all("p", recursive=False)

    # print("Body Tag Found:", title_div is not None)  # Debugging print
    for p in p_container:
        # Try to find the next link to scrape
        a_tag = p.find("a")
        if (a_tag is None):
            print("Couldn't find a_tag!")

        # If there's no <a> link, use the paragraph text
        if (a_tag is None):
            next_link_name = p.get_text()
        else:
            next_link_name = a_tag.get_text()

        # Find level classifier
        if ("Article" in next_link_name):
            node_level_classifier = "ARTICLE"
        elif ("Chapter" in next_link_name):
            node_level_classifier = "CHAPTER"
            if ("RESERVED" in next_link_name):
                continue
        elif ("Title" in next_link_name):
            node_level_classifier = "TITLE"
    
        number = next_link_name.split(" ")[-1]
        # If there's no a_tag, set the name manually
        if a_tag:
            name = a_tag.next_sibling.strip()
        else:
            name = "Reserved"
        node_name = f"{node_level_classifier} {number} {name}"

        # We can only create the node_link if a_tag is real
        if a_tag:
            href_link = a_tag['href']
            node_link = BASE_URL + href_link
        else:
            node_link = url

       
        # You can possibly change the node_type if it's reserved, if you want
        node_type = "structure"
        node_id = f"{node_parent}{node_level_classifier}={number}/" 
        
        node_text = None
        node_citation = None
        node_addendum = None

        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
         ### INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
        
        # Only scrape if the next link exists, otherwise continue
        if (a_tag):
            scrape_chapters(node_link, top_level_title, node_id)


def scrape_chapters(url, top_level_title, last_node):
    response = make_request(url)
    if response is None:
        return
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')

    levels = []
    level_soups = []
    level_ids = [last_node]
    

    all_elements = soup.find_all("li", recursive=True)
    for element in all_elements:
        text = element.get_text()
        # Division 2
        node_level_classifier = text.split(" ")[0].upper()
        # DIVISION

        # [CHAPTER]
        # [TITLE=1, CHAPTER=2A/]
        # Node_parent: TITLE=1
        
        # <li ARTICLE 5>
        # <ul>
        #    <li PART 1 EDUCATION>
        #    <ul>
        #        <li SUBPART 1 Board of Education>
        #    <li PART 2 EDUCATION
        
        for tag in element.parent.previous_elements:
            if (tag.name == "li"):
                last_text = tag.get_text()
                last_level_classifier = last_text.split(" ")[0].upper()
                # ACTUALLY SHOULD BE SUBDIVISION
                if (last_level_classifier == node_level_classifier):
                    node_level_classifier = f"SUB{node_level_classifier}"
                break
                    
        # SECTION
        new_level = False
        if (node_level_classifier not in levels):
            if (node_level_classifier != "SECTION"):
                levels.append(node_level_classifier)
                level_soups.append(element)
            # Right here
            node_parent = level_ids[-1]
            new_level = True
     
        else:
            index = levels.index(node_level_classifier)
            # index = 0
            # TITLE=1
            node_parent = level_ids[index]

        if node_level_classifier == "SECTION":
            a_tag = element.find("a") 
            href_link = a_tag['href']
            found_node_name = element.get_text()
            new_url = BASE_URL + href_link
            scrape_section(new_url, top_level_title, node_parent, found_node_name)
            continue    
        
        # Add your node here
        node_type = "structure"
        node_name = text
        node_level_number = text.split(" ")[1]
        node_id = f"{node_parent}{node_level_classifier}={node_level_number}/"
        # TITLE=1/CHAPTER=2A/
        node_link = url
        
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
         ### INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue
            
        if new_level:
            level_ids.append(node_id)
        else:
            # Every time we replace an item, chop off the end of the list
            level_ids[index+1] = node_id
            level_ids = level_ids[0:index+2]
            levels = levels[0:index+1]
            level_soups = level_soups[0:index+1]


def scrape_section(new_url, top_level_title, node_parent, found_node_name):
    response = make_request(new_url)
    if response is None:
        print("Found Invalid Link!")
        print(new_url + top_level_title + node_parent)
        node_name = found_node_name
        node_type = "url-broken"
        node_level_classifier = "SECTION"
        node_link = new_url
        section_number_id = new_url.split('-')[-1].replace(".html", "")
        node_id = f"{node_parent}SECTION={section_number_id}"
        ### FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        return

    data = response.read()      # a `bytes` object

    data = data.replace(b'\xa7', '§'.encode('utf-8'))
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, 'html.parser')


    section_container = soup.find("head")
        
    node_link = new_url

    node_text = []
    node_type = "content" 
    node_level_classifier = "SECTION"
    # Make a citation
    node_addendum = None

    page_content = soup.find("body")

    if not page_content or page_content.get_text().strip() == "":
        print("Found Blank!")
        print(new_url + top_level_title + node_parent)
        node_name = found_node_name
        node_type = "blank"
        node_level_classifier = "SECTION"
        node_link = new_url
        section_number_id = new_url.split('-')[-1].replace(".html", "")
        node_id = f"{node_parent}SECTION={section_number_id}"
        node_data = (node_id, top_level_title, node_type, node_level_classifier, None, None, None, node_link, None, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
        insert_node_ignore_duplicate(node_data)
        return
    
    else:
        section_numb = section_container.find("title")
        section_number_add = section_numb.get_text().strip()
        section_number = section_number_add.split(" ")[-1]
        node_citation = f"Al. Stat. § {section_number}"
        node_name = "Section " + section_number + " - "

        section_text_container = soup.find("body")

        section_name = section_text_container.find("h4")
        section_name_add = section_name.get_text().strip()
        node_name += section_name_add

        
        # Need to loop over every html element in sectionBody
        for i, element in enumerate(section_text_container.find_all("p", recursive=False)):
            current_text = element.get_text().strip()
            node_text.append(current_text)

        history = soup.find("i")
            
        if history is None:
            pass
        else:
            node_addendum = history.get_text().strip()
        
        node_tags = None
        
        section_number_id = section_number.split('-')[-1]
        node_id = f"{node_parent}SECTION={section_number_id}"
        ### FOR ADDING A CONTENT NODE, allowing duplicates
        node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
        base_node_id = node_id
        
        for i in range(2, 10):
            try:
                insert_node(node_data)
                #print("Inserted!")
                break
            except Exception as e:   
                print(e)
                node_id = base_node_id + f"-v{i}/"
                node_type = "content_duplicate"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
            continue






# Decorator to implement exponential backoff retry strategy
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
        else:
            # Re-raise the exception if it's not a 404 error
            raise





    
    

if __name__ == "__main__":
     main() 