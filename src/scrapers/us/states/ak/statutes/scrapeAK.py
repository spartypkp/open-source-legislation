import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import json
from bs4.element import Tag
import asyncio


TABLE_NAME = "ak_node"
BASE_URL = "https://www.akleg.gov"
TOC_URL = "https://www.akleg.gov/basis/statutes.asp"
SKIP_TITLE = 0 # 0/47 titles
DRIVER = None
RESERVED_KEYWORDS = ["Repealed"]


def main():
    insert_jurisdiction_and_corpus_node()
    scrape_all_titles()

def scrape_all_titles():
    global DRIVER
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)

    og_parent = "ak/statutes/"
    
    toc_nav_container = DRIVER.find_element(By.ID, "TOC_A")
    toc_nav_container.click()
    
    
    for i in range(SKIP_TITLE, 47):
        time.sleep(2)
        titles_container = DRIVER.find_element(By.ID, "TitleToc")
        all_titles = titles_container.find_elements(By.TAG_NAME, "li")
        title_container = all_titles[i]
        title_a_tag = title_container.find_element(By.TAG_NAME, "a")
        title_name = title_a_tag.text.strip()
        top_level_title = title_name.split(" ")[1]
        if top_level_title[-1] == ".":
            top_level_title = top_level_title[:-1]
        
        # I want to convert top level title to a string with leading zeros ex: 1 -> 01, 21 -> 21
        
        
        node_citation = top_level_title.zfill(2)
        node_link = TOC_URL + "#" + node_citation
        node_type = "structure"
        node_level_classifier = "TITLE"
        title_node_id = f"{og_parent}{node_level_classifier}={top_level_title}/"
        

        ### Get title information, Add title node
        title_node_data = (title_node_id, top_level_title, node_type, node_level_classifier, None, None, "AS " + node_citation, node_link, None, title_name, None, None, None, None, None, og_parent, None, None, None, None, None)
        print(title_node_id)
        insert_node_ignore_duplicate(title_node_data)

        # Find the parent element of the title container, using By.XPATh
        title_container.click()
        title_a_tag.click()
        time.sleep(0.5)
        

        scrape_all_chapters(top_level_title, title_node_id, node_citation)
        title_return = DRIVER.find_element(By.ID, "titleLink")
        title_return.click()
        time.sleep(0.5)

def scrape_all_chapters(top_level_title, node_parent, parent_citation):
    global DRIVER
    
    chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
    
    _all_chapters = len(chapters_container.find_elements(By.TAG_NAME, "a"))

    

    for i in range(0, _all_chapters):
        #print(i)
        chapters_container = DRIVER.find_element(By.ID, "ChapterToc")
        all_chapters = chapters_container.find_elements(By.TAG_NAME, "li")
        chapter_container = all_chapters[i]
        chapter_a_tag = chapter_container.find_element(By.TAG_NAME, "a")
        chapter_a_soup = BeautifulSoup(chapter_a_tag.get_attribute("outerHTML"), features="html.parser")
        #print(chapter_a_soup.prettify())

        chapter_name = chapter_a_soup.get_text()
        #print(f"Chapter: {chapter_name}")
        if "No Sections" in chapter_name:
            return
        chapter_number = chapter_name.split(" ")[1]
        if chapter_number[-1] == ".":
            chapter_number = chapter_number[:-1]
        
        node_type = "structure"
        node_level_classifier = "CHAPTER"
        
        node_citation =  parent_citation + "." + chapter_number
        chapter_number = str(int(chapter_number))
        node_link = TOC_URL + "#" + node_citation
        
        for word in RESERVED_KEYWORDS:
            if word in chapter_name:
                node_type = "reserved"
                break
        node_id = f"{node_parent}{node_level_classifier}={chapter_number}/"
        node_data =  (node_id, top_level_title, node_type, node_level_classifier, None, None, "AS " + node_citation, node_link, None, chapter_name, None, None, None, None, None, node_parent, None, None, None, None, None)

         ## INSERT STRUCTURE NODE, if it's already there, skip it
        try:
            insert_node(node_data)
            print(node_id)
        except:
            print("** Skipping:",node_id)
            continue

        if node_type!="reserved":
            chapter_container.click()
            chapter_a_tag.click()
            time.sleep(1)
            scrape_all_sections(top_level_title, node_id)
            chapter_return = DRIVER.find_element(By.ID, "partHead").find_element(By.TAG_NAME, "a")
            chapter_return.click()

        time.sleep(1)
        
def scrape_all_sections(top_level_title, node_parent):
    
    sections_container = DRIVER.find_element(By.ID, "ChapterToc")
    
    _all_sections = sections_container.find_elements(By.TAG_NAME, "a")

    # can I call this concurrently with
    for i in range(0, len(_all_sections)):

        sections_container = DRIVER.find_element(By.ID, "ChapterToc")
        try:

            all_sections = sections_container.find_elements(By.TAG_NAME, "a")
            section_container_raw = all_sections[i]
            section_container = BeautifulSoup(section_container_raw.get_attribute("outerHTML"), features="html.parser")

        
            
            node_name = section_container.get_text().strip()
            
            if "No Sections" in node_name:
                return
            
            node_number = node_name.split(" ")[1]
            found_article = False
            
            if node_number[-1] == ".":
                node_number = node_number[:-1]
            
            node_citation = node_number

            node_number = node_number.split(".")[-1]
            # Remove any leading zeros ex: 005 -> 5
            node_number = str(int(node_number))
            

            
            node_type = "content"
            node_level_classifier = "SECTION"
            node_link = TOC_URL + "#" + node_citation

            for word in RESERVED_KEYWORDS:
                if word in node_name:
                    node_type = "reserved"
                    break

            node_text = None
            node_addendum = None
            node_tags = None
            node_references = None
            #node_tags = None
            #print(node_type)
            if node_type != "reserved":
                node_text = []
                node_addendum = None
                node_references = {}
                node_tags = {}

                # https://www.akleg.gov/basis/statutes.asp#02.15.010
                

                section_driver = webdriver.Chrome()
                section_driver.get(node_link)
                section_driver.implicitly_wait(1)
                time.sleep(1)
                section_driver.find_element(By.ID, "content")

                
                
                for i in range(0, 100):
                    time.sleep(.25)
                    try:
                        addendum_container_raw = section_driver.find_element(By.ID, "sideSection")
                        addendum_container = addendum_container_raw.find_element(By.TAG_NAME, "div")
                        # print(addendum_container.get_attribute("outerHTML"))
                        break
                    except:
                        print(i*.25)
                        addendum_container = None
                

                
                
                section_soup = BeautifulSoup(section_driver.page_source, features="html.parser").body
                
                
                all_text_container = section_soup.find(id="content")
                
                text_container = all_text_container.find("a", attrs={"name": node_citation})
                iterator = text_container.parent

                # Find parent article
                for tag in iterator.previous_elements:
                    if not isinstance(tag, Tag):
                        continue
                    
                    if tag.find("h7") is not None:
                        article_container = tag.find("h7")
                        article_name = article_container.get_text().strip()
                        article_number = article_name.split(" ")[1]
                        if article_number[-1] == ".":
                            article_number = article_number[:-1]
                        article_node_type = "structure"
                        article_node_level_classifier = "ARTICLE"
                        

                        article_node_id = f"{node_parent}{article_node_level_classifier}={article_number}/"
                        article_node_data =  (article_node_id, top_level_title, article_node_type, article_node_level_classifier, None, None, None, node_link, None, article_name, None, None, None, None, None, node_parent, None, None, None, None, None)

                        ## INSERT STRUCTURE NODE, if it's already there, skip it
                        insert_node_ignore_duplicate(article_node_data, quiet=True)
                        
                        found_article = True
                        break

                internal = []
                external = []
                
                while True:
                    iterator = iterator.next_sibling
                    if iterator is None:
                        break
                    if isinstance(tag, Tag):
                    
                        if iterator.name == "b":
                            break
                        txt = iterator.get_text().strip()
                        if iterator.name == "a":
                            href = iterator["href"]
                            
                            if "#" in href:
                                ref_link = "https://www.akleg.gov/basis/" + href
                                internal.append({"citation": txt, "link": ref_link})
                            else:
                                external.append({"text": txt, "link": href})
                        if txt == "":
                            continue
                        node_text.append(txt)
                    else:

                        txt = iterator
                        print(txt)
                        if txt == "":
                            continue

            
                
                
                addendum_container = BeautifulSoup(addendum_container.get_attribute("outerHTML"), features="html.parser").find("div")
                
                if addendum_container is not None:
                    
                    category = None
                    for i, element in enumerate(addendum_container.contents):
                        
                        if isinstance(element, Tag):
                            if element.name == "br":
                                continue
                            txt = element.get_text().strip()
                            print(txt)
                            if element.name == "h5":
                                category = element.get_text().strip()
                                continue
                            
                            if element.name == "a":
                                href = element["href"]
                                tag_link = "https://www.akleg.gov/basis/" + href
                                
                                if "REFERENCES" in category:
                                    if "#" in href:
                                        
                                        internal.append({"citation": txt, "link": tag_link})
                                    else:
                                        external.append({"text": txt, "link": href})

                                if category not in node_tags:
                                    node_tags[category] = []
                                

                                node_tags[category].append({"citation": txt, "link": tag_link})
                                print("ADDING TO NODE_TAGS")
                        else:
                            txt = element
                            print(txt)
                            if txt == "":
                                continue
                            if "History." in txt:
                                node_addendum = txt
                                break
                            if "REFERENCES" in category:
                                continue

                            node_tags[category][-1]['text'] = txt   

                
                print("NODE TAGS", node_tags) 
                if node_tags == {}:
                    node_tags = None
                else:
                    node_tags = json.dumps(node_tags)

                if len(internal) > 0:
                    node_references["internal"] = internal
                if len(external) > 0:
                    node_references["external"] = external
                if node_references == {}:
                    node_references = None
                else:
                    node_references = json.dumps(node_references)

            if found_article:
                node_id = f"{article_node_id}{node_level_classifier}={node_number}"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, "AS " + node_citation, node_link, node_addendum, node_name, None, None, None, None, None, article_node_id, None, None, node_references, None, node_tags)

            else:
                node_id = f"{node_parent}{node_level_classifier}={node_number}"
                node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, "AS " +node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)




            
            ### FOR ADDING A CONTENT NODE, allowing duplicates
            base_node_id = node_id
            
            for i in range(2, 10):
                try:
                    insert_node(node_data)
                    print(node_id)
                    break
                except Exception as e:   
                    print(e)
                    node_id = base_node_id + f"-v{i}/"
                    node_type = "content_duplicate"
                    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
                continue
        except:
            continue
        



# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ak/",
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
        "ak/statutes/",
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
        "ak/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)

def insert_node_ignore_duplicate(row_data, quiet=False):
    try:
        util.insert_row_to_local_db(, TABLE_NAME, row_data)
    except psycopg2.errors.UniqueViolation as e:
        if not quiet:
            print(e)
    return


    

# async def fetch(session, url):
#     async with session.get(url) as response:
#         return await response.text()

# def parse(html):
#     soup = BeautifulSoup(html, features="html.parser")
    

#     all_sections = sections_container.find_elements(By.TAG_NAME, "a")
#     section_container = all_sections[i]

#     node_name = section_container.text.strip()
#     print(node_name)
    
#     node_number = node_name.split(" ")[1]
    
#     if node_number[-1] == ".":
#         node_number = node_number[:-1]
    
#     node_citation = node_number

#     node_number = node_number.split(".")[-1]
#     # Remove any leading zeros ex: 005 -> 5
#     node_number = str(int(node_number))
#     print(node_number)
    
#     node_type = "content"
#     node_level_classifier = "SECTION"
#     node_link = TOC_URL + "#" + node_citation

#     for word in RESERVED_KEYWORDS:
#         if word in node_name:
#             node_type = "reserved"
#             break

#     node_text = None
#     node_addendum = None
#     node_references = None
#     node_tags = None

#     if node_type != "reserved":
#         node_text = []
#         node_addendum = ""
#         node_references = {}
#         node_tags = {}

#         # https://www.akleg.gov/basis/statutes.asp#02.15.010
        
#         response = urllib.request.urlopen(node_link)
#         await asyncio.sleep(2)
#         data = response.read()      # a `bytes` object
#         text = data.decode('utf-8') # a `str`; 
#         section_soup = BeautifulSoup(text, features="html.parser").body
        
        
#         all_text_container = section_soup.find(id="content")
        
#         text_container = all_text_container.find("a", attrs={"name": node_citation})
#         iterator = text_container.parent

#         # Find parent article
#         for tag in iterator.previous_elements:
#             if not isinstance(tag, Tag):
#                 continue
            
#             if tag.find("h7") is not None:
#                 article_container = tag.find("h7")
#                 article_name = article_container.get_text().strip()
#                 article_number = article_name.split(" ")[1]
#                 if article_number[-1] == ".":
#                     article_number = article_number[:-1]
#                 article_node_type = "structure"
#                 article_node_level_classifier = "ARTICLE"
#                 node_citations = node_citation.split(".").pop()
#                 article_node_citation = ".".join(node_citations)

#                 article_node_id = f"{node_parent}{article_node_level_classifier}={article_number}/"
#                 article_node_data =  (article_node_id, top_level_title, article_node_type, article_node_level_classifier, None, None, article_node_citation, node_link, None, article_name, None, None, None, None, None, node_parent, None, None, None, None, None)

#                 ## INSERT STRUCTURE NODE, if it's already there, skip it
#                 insert_node_ignore_duplicate(article_node_data, quiet=True)
                
#                 found_article = True
#                 break

#         internal = []
#         external = []
        
#         while True:
#             iterator = iterator.next_sibling
#             if isinstance(tag, Tag):
                
#                 if iterator.name == "b":
#                     break
#                 txt = iterator.get_text().strip()
#                 if iterator.name == "a":
#                     href = iterator["href"]
                    
#                     if "#" in href:
#                         ref_link = "https://www.akleg.gov/basis/" + href
#                         internal.append({"citation": txt, "link": ref_link})
#                     else:
#                         external.append({"text": txt, "link": href})

#                 node_text.append(txt)
#             else:

#                 txt = iterator
#                 print(txt)
#                 if txt == "":
#                     continue

    
        
#         addendum_container_raw = section_soup.find(id="sideSection")
        
#         for i in range(0, 5):
#             time.sleep(.25)
#             addendum_container = addendum_container_raw.find("div")
#             if addendum_container is not None:
#                 break

#         if addendum_container is not None:
            
#             category = None
#             for i, element in enumerate(addendum_container.find_all(recursive=False)):
#                 if isinstance(element, Tag):
#                     if element.name == "br":
#                         continue
#                     if element.name == "h5":
                        
#                         category = element.get_text().strip()

#                         continue
#                     txt = element.get_text().strip()
#                     if element.name == "a":
#                         href = element["href"]
#                         tag_link = "https://www.akleg.gov/basis/" + href
                        
#                         if "REFERENCES" in category:
#                             if "#" in href:
                                
#                                 internal.append({"citation": txt, "link": tag_link})
#                             else:
#                                 external.append({"text": txt, "link": href})

#                         if category not in node_tags:
#                             node_tags[category] = []
                        

#                         node_tags[category].append({"citation": txt, "link": tag_link})
#                 else:
#                     txt = element
#                     if txt == "":
#                         continue
#                     if "History." in txt:
#                         node_addendum = txt
#                         break
#                     if "REFERENCES" in category:
#                         continue

#                     node_tags[category][-1]['text'] = txt     
                
#         if node_tags == {}:
#             node_tags = None
#         else:
#             node_tags = json.dumps(node_tags)

#         if len(internal) > 0:
#             node_references["internal"] = internal
#         if len(external) > 0:
#             node_references["external"] = external
#         if node_references == {}:
#             node_references = None
#         else:
#             node_references = json.dumps(node_references)

#     if found_article:
#         node_id = f"{article_node_id}{node_level_classifier}={node_number}"
#     else:
#         node_id = f"{node_parent}{node_level_classifier}={node_number}"



    
#     ### FOR ADDING A CONTENT NODE, allowing duplicates
#     node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
#     base_node_id = node_id
    
#     for i in range(2, 10):
#         try:
#             insert_node(node_data)
#             print(node_id)
#             break
#         except Exception as e:   
#             print(e)
#             node_id = base_node_id + f"-v{i}/"
#             node_type = "content_duplicate"
#             node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
#         continue


# async def fetch_and_parse(session, url):
#     html = await fetch(session, url)
#     paras = parse(html)
#     return paras

# async def scrape_urls(urls):
#     async with aiohttp.ClientSession() as session:
#         return await asyncio.gather(
#             *(fetch_and_parse(session, url) for url in urls)
#         )


if __name__ == "__main__":
    main()