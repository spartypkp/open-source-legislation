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
import psycopg2
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util


 = "will2"
TABLE_NAME = "usc_node"
BASE_URL_START = "https://uscode.house.gov/browse/prelim@"
BASE_URL_END = "&edition=prelim"
TEMP_SOUP = BeautifulSoup("<b></b>", 'html.parser')

# title, subtitle, chapter, subchapter, part, subpart, division, subdivision
LEVELS = ["subtitle", "part", "subpart","chapter", "subchapter",  "section", "subsection"]

def main():
    insert_jurisdiction_and_corpus_node()
    for i in range(25, 55):
        top_level_title = "{:02d}".format(i)
        print(top_level_title)
        scrape_title(top_level_title)

def scrape_title(top_level_title):
    node_parent = "us/usc/"
    try:
        with open(f"{DIR}/data/usc{top_level_title}.xml","r") as read_file:
            text = read_file.read()
    except:
        return
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find("title")
    title_num = soup.num['value']
    title_name = soup.num.get_text() + soup.heading.get_text()
    all_notes = soup.find_all("note", recursive=False)
    title_addendum = ""
    for note in all_notes:
        title_addendum += note.get_text() + "\n"
    title_node_id = f"{node_parent}TITLE={title_num}/"
    node_type = "structure"
    node_level_classifier="title"

    print(title_num, title_name)
    print(title_addendum)
    # https://uscode.house.gov/browse/prelim@title1&edition=prelim
    link = f"{BASE_URL_START}title{title_num}{BASE_URL_END}"
    title_data = (title_node_id, title_num, node_type, node_level_classifier, None, None, None, link, title_addendum, title_name, None, None, None, None, None, node_parent, None, None, None, None, None)
    insert_node_ignore_duplicate(title_data)
    scrape(soup, title_node_id, title_num, link)
    

def scrape(current_node, node_parent, top_level_title, node_parent_link):
    all_nodes = current_node.find_all(["chapter", "subchapter", "part", "subpart", "section"], recursive=False)
    for node in all_nodes:
        if (node.name == "section"):
            # Scrape section
            print(node)
            
                
            node_num = node.num['value']
            node_name = node.num.get_text() + node.heading.get_text()
            node_level_classifier = node.name
            node_link =  f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{top_level_title}-section{node_num}&num=0&edition=prelim"
            node_id = f"{node_parent}{node_level_classifier.upper()}={node_num}"
            print(node_id)
            node_type = "content"
            node_text = None
            node_tags = None
            node_citation = None
            node_references = None
            node_addendum = None
            internal_references = []
            external_references = []
            if "status" in node.attrs:
                node_type = "reserved"
                
            else:
                node_citation = f"{top_level_title} U.S.C. § {node_num}"
                # https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section101&num=0&edition=prelim
                try:
                    node_addendum = node.find("sourcecredit").get_text()
                except:
                    node_addendum = None
                
                node_type = "content"
                node_text = []
                node_references = {}
                internal_references = []
                external_references = []
                #print(node)
                parent_content = TEMP_SOUP.new_tag('content')
                for tag in node.find_all(recursive=False):
                    #print(tag.name)
                    if tag.name == "subsection":
                        parent_content.append(tag)
                    elif tag.name == "content":
                        parent_content = tag
                        break
                            
                
                scrape_section(parent_content, node_text, internal_references, external_references)
                node_references = {}
                if internal_references:
                    node_references['internal'] = internal_references
                if external_references:
                    node_references['external'] = external_references
                if node_references:
                    node_references = json.dumps(node_references)
                else:
                    node_references = None

                node_tags = None
                if node.notes is not None:
                    all_notes = node.notes.find_all("note", recursive=False)    
                    node_tags = {}
                    for note in all_notes:
                        note_type = note['topic']
                        try:
                            note_role = note['role']
                            if note_role and note_role == "crossHeading":
                                continue
                        except:
                            pass
                        if note_type not in node_tags:
                            node_tags[note_type] = []
                        if note.heading is not None:
                            note_name = note.heading.get_text()
                        else:
                            note_name = note_type
                        note_text, note_internal_references, note_external_references, note_quoted = scrape_note(note, [], [], [])

                        note_dict = {"name": note_name, "text": note_text}
                        if note_internal_references:
                            note_dict['internal_references'] = note_internal_references
                        if note_external_references:
                            note_dict['external_references'] = note_external_references
                        if(note_quoted['act_name']):
                            note_dict['alternate_name_act'] = note_quoted
                        
                        node_tags[note_type].append(note_dict)

                    node_tags = json.dumps(node_tags)
            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
            for i in range(2, 10):
                try:
                    insert_node(node_data)
                    break
                except:
                    node_id = node_id[:-1] + f"-v{i}"
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
                continue
        else:
            node_num = node.num['value']
            node_name = node.num.get_text() + node.heading.get_text()
            node_level_classifier = node.name
            node_citation = None
            node_link =  node_parent_link.replace(BASE_URL_END, "") + f"/{node_level_classifier}{node_num}{BASE_URL_END}"
            node_addendum = ""
            node_id = f"{node_parent}{node_level_classifier.upper()}={node_num}/"
            print(node_id)
            node_type = "structure"
            node_text = None

            node_tags = None



            node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
            for i in range(2, 10):
                try:
                    insert_node(node_data)
                    break
                except:
                    node_id = node_id[:-1] + f"-v{i}"
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            scrape(node, node_id, top_level_title, node_link)


        
def scrape_section(node, node_text, internal_references, external_references):
    
    
    all_node_text = node.find_all(recursive=False)
    
    for p in all_node_text:
        if p.find("ref") is not None:
            for ref in p.find_all("ref"):
                if 'href' not in ref.attrs:
                    continue
                og_citation = ref['href']
                ref_text = ref.get_text()
                if "usc" in ref['href']:
                    ref_id_lst = ref['href'].split("/")
                    section = ref_id_lst.pop().replace("s","", 1)
                    title = None
                    while ref_id_lst:
                        txt = ref_id_lst.pop()
                        if(txt[0] == "t"):
                            title = txt.replace("t","")
                            break
                    reference_citation = f"{title} U.S.C. § {section}"
                    internal_references.append([reference_citation, og_citation, ref_text])
                else:
                    external_references.append([og_citation, ref_text])

        node_text.append(p.get_text().strip())
    
    
    return (node_text, internal_references, external_references)


def scrape_note(node, node_text, internal_references, external_references):
    
    
    all_node_text = node.find_all(recursive=False)
    note_quoted = {"act_name": "", "note_text": "", "origin": ""}
    if node.find("quotedContent") is not None:
        quotedContent = node.find("quotedContent")
        quoted_text = quotedContent.get_text().strip()
        pattern = re.compile(r"may be cited as the ‘([^’]+)’")
        match = pattern.search(quoted_text)
        
        if match:
            cited_as = match.group(1)
            note_quoted['act_name'] = cited_as
        note_quoted['note_text'] = quoted_text
        note_quoted['origin'] = p['origin']


    for p in all_node_text:

        if p.find("ref") is not None:
            for ref in p.find_all("ref"):
                if 'href' not in ref.attrs:
                    continue
                og_citation = ref['href']
                ref_text = ref.get_text()
                if "usc" in ref['href']:
                    ref_id_lst = ref['href'].split("/")
                    section = ref_id_lst.pop().replace("s","")
                    title = ref_id_lst.pop().replace("t","")
                    reference_citation = f"USC {title} § {section}"
                    internal_references.append([reference_citation, og_citation, ref_text])
                else:
                    external_references.append([og_citation, ref_text])

        node_text.append(p.get_text().strip())
    
    
    return (node_text, internal_references, external_references, note_quoted)



    


def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "us/",
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
        "us/usc/",
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
        "us/",
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
    
    




    
if __name__ == "__main__":
    main()