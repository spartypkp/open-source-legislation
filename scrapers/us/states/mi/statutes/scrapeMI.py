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
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util


# Define the type of exception you want to retry on.
# In this case, we are retrying on URLError which can be thrown by urllib.request.urlopen
from urllib.error import URLError

DIR = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://www.legislature.mi.gov/(S(4epzzujjm44fvdwoa0dbnaoi))/"
TABLE_NAME = "mi_node"

def main():
    # insert_jurisdiction_and_corpus_node()
    # open txt file
    with open(f"{DIR}/data/top_level_titles.txt") as text_file:
        next(text_file)
        for i, line in enumerate(text_file):
            url = line
            if ("chapters-" in url):
                top_level_title = url.split("chapters-")[-1].strip()
            else:
                top_level_title = url.split("chap")[-1].strip()
        
            
            # Wont work if top_level_title can't be converted to an int
            # line_in_text_file = 0
            # if(i < line_in_text_file):
            #     continue
            
            # exit(1)
            scrape_per_title(url, top_level_title, "mi/statutes/", ())



# Go to the chapter index and get all links 
def read_all_top_level_titles():
    url = "https://www.legislature.mi.gov/(S(4epzzujjm44fvdwoa0dbnaoi))/mileg.aspx?page=ChapterIndex"

    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find(id="frg_chapterindex_ChapterList_Results")
    all_links = soup.find_all("a")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            output_link = BASE_URL + link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()

# CREATE TABLE mi_node (
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

# Hardcoded Level Classifiers

# Mid Level:
# - Division: "DIVISION"
# - Act (Other Stuff): "ACT"
# Bottom Level "SECTION"

# "ACT=Act_78_of_1945/"
# "ACT= "J.R.""

# Scrapes all nodes for a given top level title. Provide the url and the name
def scrape_per_title(url, top_level_title, node_parent, past_row):
    
    emdash = '\u2014'
    emdash_encoded = urllib.parse.quote(emdash)
    

    if emdash in url:
        emdash_encoded = urllib.parse.quote(emdash)
        url = url.replace(emdash, emdash_encoded)  


    try:
        response = make_request(url)
        data = response.read()      # a `bytes` object
        text = data.decode('utf-8') # a `str`; 
        soup = BeautifulSoup(text, 'html.parser')
    # Process the response here
    except URLError as e:
        # Handle the error after the final retry attempt has failed
        print(f"Failed to retrieve the URL: {e}")
        exit(1)
        
        

    document_name = soup.find(id="frg_getmcldocument_DocumentName")
    document_name_text = document_name.get_text().strip()
    # Handle scraping a section, then return
    
    if ("§" in document_name_text or "Section" in document_name_text):
        

        # Basic Node Information
        node_type = "content"
        node_level_classifier = "SECTION"
        node_link = url

        # Node graph traversal stuff
        if "," in document_name_text:
            section_number= document_name_text.split('Section ')[-1]
        else: 
            section_number = document_name_text.split(" ")[-1]

        print(section_number)
        node_id = node_parent + node_level_classifier + "=" + section_number
        
        # Node Processing Stuff - Leave this be!
        node_text_embedding = None
        node_name_embedding = None
        node_summary = None
        node_summary_embedding = None
        node_hyde = None
        node_hyde_embedding = None
        node_direct_children = None
        node_siblings = None
        node_references = None
        node_incoming_references = None
        node_tags = None

        # Metadata we have to extract
        node_text = []
        node_citation = None
        node_addendum = None
        if ("§" in document_name_text):
            node_name = document_name_text.split("§")[0]
        else:
            node_name = ""
        # Chapter 1 Section 1
        # Top_level_title § section_number
        # (1 § 1)
        section = soup.find(id="frg_getmcldocument_MclContent")
        section_tags = section.find_all(recursive=False)
        for i, tag in enumerate(section_tags):
            if i < 3:
                continue
            elif i == 3:
                node_name += tag.get_text().strip()
            # Div, this is the section text
            elif tag.name == "div":
                current_text = tag.get_text().strip()
                node_text.append(current_text)
                # Optionally clean the text. Remove extra whitespace, "\n", "&nbsp;"
            # Font element, this is node addendum stuff
            elif tag.name == "font":
                current_text = tag.get_text()
                current_text = current_text.split("Constitutionality:")
                node_addendum = current_text[0]
                extra = current_text[-1]
                if (node_tags is None):
                    node_tags = {}
                node_tags["Constitutionality:"] = extra
                node_tags = json.dumps(node_tags)
                break
                # Also clean the text
            else:
                current_text = tag.get_text().strip()
                if (current_text == ""):
                    continue
                node_text.append(current_text)
                
        # Add our node to the database
        node_id = insert_row_data(node_id,top_level_title,node_type,node_level_classifier,node_text,node_text_embedding,node_citation,node_link,node_addendum,node_name,node_name_embedding,node_summary,node_summary_embedding,node_hyde,node_hyde_embedding,node_parent,node_direct_children,node_siblings,node_references,node_incoming_references,node_tags)
        
        return
    
    # Top level title Chapter
    if ("Chapter" in document_name_text):
        node_type = "structure"
        node_level_classifier = "CHAPTER"
        node_link = url

        # Node graph traversal stuff
        chapter_number = document_name_text.split(" ")[-1]
        node_id = node_parent + node_level_classifier + "=" + chapter_number + "/"
        
        # Node Processing Stuff - Leave this be!
        node_text_embedding = None
        node_name_embedding = None
        node_summary = None
        node_summary_embedding = None
        node_hyde = None
        node_hyde_embedding = None
        node_direct_children = None
        node_siblings = None
        node_references = None
        node_incoming_references = None
        node_tags = None

        # Metadata we have to extract
        node_text = None
        node_citation = None
        node_addendum = None
        node_name = "placeholder"
        title = soup.find(id="frg_getmcldocument_MclContent")
        title_tags = title.find_all(recursive=True)
        for temp in title_tags:
            text = temp.get_text(separator='|').split('|')
            node_name = text[1].strip()
            break
        node_id = insert_row_data(node_id,top_level_title,node_type,node_level_classifier,node_text,node_text_embedding,node_citation,node_link,node_addendum,node_name,node_name_embedding,node_summary,node_summary_embedding,node_hyde,node_hyde_embedding,node_parent,node_direct_children,node_siblings,node_references,node_incoming_references,node_tags)
        
        node_parent = node_id
    elif past_row:
        summary = soup.find(id="frg_getmcldocument_MclContent")
        texts = [str(element).strip() for element in summary if isinstance(element, NavigableString)]

        # Now `texts` will contain only the text nodes directly under the <span>, excluding child elements.
        # You can join them into a single string if needed
        past_node_summary = ' '.join(texts)
        
        # Font tag
        try:
            past_node_addendum = summary.find("font").get_text()
        except:
            past_node_addendum = None

        last_node_id, last_top_level_title, last_node_type, last_node_level_classifier, last_node_text, last_node_text_embedding, last_node_citation, last_node_link,last_node_addendum,last_node_name,last_node_name_embedding,last_node_summary,last_node_summary_embedding,last_node_hyde,last_node_hyde_embedding,last_node_parent,last_node_direct_children,last_node_siblings,last_node_references,last_node_incoming_references,last_node_tags = past_row
        last_node_addendum = past_node_addendum
        last_node_summary = past_node_summary
        last_node_id = insert_row_data(last_node_id, last_top_level_title, last_node_type, last_node_level_classifier, last_node_text, last_node_text_embedding, last_node_citation, last_node_link,last_node_addendum,last_node_name,last_node_name_embedding,last_node_summary,last_node_summary_embedding,last_node_hyde,last_node_hyde_embedding,last_node_parent,last_node_direct_children,last_node_siblings,last_node_references,last_node_incoming_references,last_node_tags)
        
        node_parent = last_node_id
        past_row = ()

        

                    #id="frg_getmcldocument_MclChildren")
    soup = soup.find(id="frg_getmcldocument_MclChildren")
    tr_tags = soup.find_all('tr')
    
    for i, tr in enumerate(tr_tags):
        if i == 0:
            continue
        
        node_name = None
        node_link = None
    
        children_list = list(tr.children)
        
             
        document_col = children_list[1].get_text()
        type_col = children_list[2].get_text()
        description_col = children_list[3].get_text()

        a_tag = tr.find('a')
        if a_tag and a_tag.text:
            node_name = a_tag.get_text().strip()
            node_link = BASE_URL + a_tag['href']
        
        if type_col == "Division":
            node_level_classifier = "DIVISION"
        else:
            node_level_classifier = "ACT"
        
        node_type = "structure"
        node_id = node_parent + node_level_classifier + "=" + node_name.replace(" ", "_") + "/"
        
        # Node Processing Stuff - Leave this be!
        node_text_embedding = None
        node_name_embedding = None
        node_summary = None
        node_summary_embedding = None
        node_hyde = None
        node_hyde_embedding = None
        node_direct_children = None
        node_siblings = None
        node_references = None
        node_incoming_references = None
        node_tags = None

        # Metadata we have to extract
        node_text = None
        # Don't worry about node citation for structurenodes
        node_citation = None
        # Don't worry about for structure nodes
        node_addendum = None
        # This should be the description column
        node_name = description_col
        
        # Repealed case
        
        if ("Repealed-" in description_col):
            print("Is repealed!")
            node_id += "-Repealed"
            node_type = "reserved"
            # Finalaze all data values, then insert for scraping
            node_id = insert_row_data(node_id,top_level_title,node_type,node_level_classifier,node_text,node_text_embedding,node_citation,node_link,node_addendum,node_name,node_name_embedding,node_summary,node_summary_embedding,node_hyde,node_hyde_embedding,node_parent,node_direct_children,node_siblings,node_references,node_incoming_references,node_tags)
            
        # Good to go
        else:
            # Create new node here (structure)
            
            link_tag = tr.find('a')
            link_text = BASE_URL + link_tag['href']
            # Finalize all data values, then insert for scraping
            row_data = (node_id,top_level_title,node_type,node_level_classifier,node_text,node_text_embedding,node_citation,node_link,node_addendum,node_name,node_name_embedding,node_summary,node_summary_embedding,node_hyde,node_hyde_embedding,node_parent,node_direct_children,node_siblings,node_references,node_incoming_references,node_tags)
            past_row = row_data
            # print(row_data)
            
            if ("Section"  in type_col):
                # Remove the last "/"
                # blah/ACT=section2/"
                # blah/
                
                past_row = ()
                node_id = node_id[0:len(node_id)-1]
                temp = node_id.split("/")
                temp.pop()
                node_id = "/".join(temp) + "/"
            

            scrape_per_title(link_text, top_level_title, node_id, past_row)
            # Url before section


# THIS FUNCTION SHOULD ONLY BE RAN ONCE PER SCRAPE
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "mi/",
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
        "mi/statutes/",
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
        "mi/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(TABLE_NAME, corpus_row_data)





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

# Example usage

def insert_row_data(node_id,top_level_title,node_type,node_level_classifier,node_text,node_text_embedding,node_citation,node_link,node_addendum,node_name,node_name_embedding,node_summary,node_summary_embedding,node_hyde,node_hyde_embedding,node_parent,node_direct_children,node_siblings,node_references,node_incoming_references,node_tags):
    if "R.S._of_1846" not in node_id:
        row_data = (node_id,
            top_level_title,
            node_type,
            node_level_classifier,
            node_text,
            node_text_embedding,
            node_citation,
            node_link,
            node_addendum,
            node_name,
            node_name_embedding,
            node_summary,
            node_summary_embedding,
            node_hyde,
            node_hyde_embedding,
            node_parent,
            node_direct_children,
            node_siblings,
            node_references,
            node_incoming_references,
            node_tags
        )
    else:
        for i in range(2, 10):
            try:
                row_data = (node_id,
                    top_level_title,
                    node_type,
                    node_level_classifier,
                    node_text,
                    node_text_embedding,
                    node_citation,
                    node_link,
                    node_addendum,
                    node_name,
                    node_name_embedding,
                    node_summary,
                    node_summary_embedding,
                    node_hyde,
                    node_hyde_embedding,
                    node_parent,
                    node_direct_children,
                    node_siblings,
                    node_references,
                    node_incoming_references,
                    node_tags
                    )
                print(row_data)
                util.insert_row_to_local_db(TABLE_NAME, row_data)
                return node_id
            except Exception:
                # "blahblah/ACT=R.S._of_1846/"
                # "blahblah/ACT=R.S._of_1846-v2/"
                node_id = node_id[0:len(node_id)-1] + f"-v{i}/"
                print("Failed to add duplicate R.S")
    print(row_data)
    util.insert_row_to_local_db(TABLE_NAME, row_data)
    return node_id
    

if __name__ == "__main__":
     main() 