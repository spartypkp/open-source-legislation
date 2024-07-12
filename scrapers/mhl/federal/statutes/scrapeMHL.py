from bs4 import BeautifulSoup, NavigableString

import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
import requests
import json
import re
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from urllib.error import URLError
from pypdf import PdfReader
import psycopg2
import asyncio
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

TABLE_NAME = "mhl_node"
 = "will2"
# ChildRightsProtectionAct i=46
#242
LAST_TITLE_INDEX = 0
# DONE = ["AdmiraltyJurisdictionAct1986_1.pdf", "AdministrationofAirportsandAirNavigationFacilitiesAct_1.pdf"]
DONE = []

async def main():
    try:
        insert_jurisdiction_and_corpus_node()
    except psycopg2.errors.UniqueViolation as e:
        print(e)
        pass
    with open(f"{DIR}/data/bad_pdfs.txt", "w") as write_file:

        with open(f"{DIR}/data/top_level_titles.txt", "r") as read_file:
            for i, line in enumerate(read_file):
                if i < LAST_TITLE_INDEX:
                    continue
                
                
                
                # exit(1)
                if(i % 2 == 0):
                    pdf_name = line.strip()
                else:
                    pdf_link = line.strip()
                    if("amendment" in pdf_name.lower()):
                        print(pdf_name)
                    # continue
                    # print(pdf_name)
                    # if(pdf_name in DONE):
                    #     print("Already scraped!")
                    #     continue
                    # if ("Act" not in pdf_name or "Amendment" in pdf_name):
                    #     write_file.write(pdf_name + "\n" + pdf_link + "\n")
                    #     continue
                    await scrape_act_pdf(pdf_name, pdf_link)
    




async def scrape_act_pdf(pdf_name, link):
    # Read pdf from pdf_name file
    reader = PdfReader(f"{DIR}/data/{pdf_name}")
    # Extract title, chapter information from toc_page
    toc_text = []
    last_toc_index = 0
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        toc_text.append(page_text)
        if ("AN ACT " in page_text):
            last_toc_index = i
            break
    
    toc_page_text = "\n".join(toc_text)
    toc_end_index = toc_page_text.find("AN ACT ")
    toc_page_text = toc_page_text[:toc_end_index]
    #print(toc_page_text)
    
   
    top_level_title, title_name, chapter_num, chapter_name, organization_structure = extract_title_information(toc_page_text)
    title_node_id = f"mhl/statutes/TITLE={top_level_title}/"
    

    # Insert title node
    title_data = (title_node_id, top_level_title, "structure", "title", None, None, None, link, None, title_name, None, None, None, None, None, "mhl/statutes/", None, None, None, None, None)
    insert_node_ignore_duplicate(title_data)

    # Insert chapter node
    chapter_node_id = f"{title_node_id}CHAPTER={chapter_num}/"
    node_tags = json.dumps({"document_source": pdf_name})
    chapter_data = (chapter_node_id, top_level_title, "structure", "chapter", None, None, None, link, None, chapter_name, None, None, None, None, None, title_node_id, None, None, None, None, node_tags)
    try:
        insert_node(chapter_data)
    except:
        print("Already scraped chapter: ", chapter_node_id)
        return
    print(organization_structure)
    structure_nodes = []
    if(type(organization_structure) == dict):
        structure_nodes.append(organization_structure)
    else:
        structure_nodes = organization_structure
    
    last_valid_page = 1
    
    for i, object in enumerate(structure_nodes):
        node_parent = chapter_node_id
        #print(object)
        level = object['level']
        level_num = object['level_num']
        level_name = object['level_name']
        child_sections = object['child_sections']
        # No level identifier, straight to sections
        
        if(level != "N/A"):
            level_node_id = f"{chapter_node_id}{level.upper()}={level_num}/"
            level_data = (level_node_id, top_level_title, "structure", level, None, None, None, link, None, level_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            while True:
                try:
                    insert_node(level_data)
                    break
                except:
                    level_node_id = level_node_id[:-1] + "-v2/"
                    level_data = (level_node_id, top_level_title, "structure", level, None, None, None, link, None, level_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            node_parent = level_node_id


        # I would like to call this function many times asynchronously, but I don't know how to do that
        tasks = []
        for i, child in enumerate(child_sections):
            use_child = child
            print(child.keys())
            if "level" in child.keys():
                level = child['level']
                level_num = child['level_num']
                level_name = child['level_name']
                child_sections_temp = child['child_sections']
                # No level identifier, straight to sections
                
                if(level != "N/A"):
                    new_level_node_id = f"{level_node_id}{level.upper()}={level_num}/"
                    level_data = (new_level_node_id, top_level_title, "structure", level, None, None, None, link, None, level_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    while True:
                        try:
                            insert_node(level_data)
                            break
                        except:
                            new_level_node_id = level_node_id[:-1] + "-v2/"
                            level_data = (new_level_node_id, top_level_title, "structure", level, None, None, None, link, None, level_name, None, None, None, None, None, node_parent, None, None, None, None, None)
                    node_parent = new_level_node_id
                    use_child = child_sections_temp

            print(use_child)
            invalidPageNum = False
            try:
                page_num = int(use_child['page_number'])
                last_valid_page = page_num
            except:
                page_num = last_valid_page
                print("Invalid page number: ", use_child)
                invalidPageNum = True
            num_pages = 2
            if(invalidPageNum):
                num_pages = 5
            if(page_num >= len(reader.pages)):
                page_num = len(reader.pages)-1
                num_pages = 1
            else:
                page_num = page_num - 1
            
            section_text = ""
            for i in range(0, num_pages):
                try:
                    section_text += reader.pages[page_num].extract_text()
                except:
                    break

            target_section = str(use_child['section_num']) + " " + use_child['section_name']
            print("Scraping target section: ", target_section)
            task = scrape_sections_async(target_section, section_text)
            tasks.append(task)

        # Execute the coroutine tasks concurrently
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            print(result)
            section_number = result['section_number'].replace("§", "").strip()
            section_node_id = f"{node_parent}SECTION={section_number}"
            section_text = result['section_text'].strip().split("\n")
            # print(section_node_id)
            # print(section_text)
            section_citation = f"RMI {top_level_title} § {section_number}"
            section_name = child_sections[i]['section_name']
            node_type = "section"
            if(section_name == "Reserved"):
                node_type = "reserved"
                section_text = None
                section_citation = None

            section_data = (section_node_id, top_level_title, node_type, "section", section_text, None, section_citation, link, None, section_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            for i in range(2, 10):
                try:
                    insert_node(section_data)
                    break
                except:
                    section_node_id = section_node_id[:-1] + f"-v{i}"
                    section_data = (section_node_id, top_level_title, node_type, "section", section_text, None, section_citation, link, None, section_name, None, None, None, None, None, node_parent, None, None, None, None, None)
            
            
        
        
    
async def scrape_sections_async(target_section, source_legislation):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, scrape_section, target_section, source_legislation)
    return result

def scrape_section(target_section, source_legislation):
    
    raw_completion = getPromptPDFSectionExtractionSmall(target_section, source_legislation)
    completion = json.loads(raw_completion)
    return completion
    
        
        
   
    







def extract_title_information(toc_page_text):
    json_completion = getPromptPDFTitleExtraction(toc_page_text)
    completion = json.loads(json_completion)
    title_num = completion['title_num']
    title_name = completion['title_name']
    chapter_num = completion['chapter_num']
    chapter_name = completion['chapter_name']
    organization_structure = completion['organization_structure']
    return title_num, title_name, chapter_num, chapter_name, organization_structure


def getPromptPDFTitleExtraction(toc_page_text):
    system = "You are a helpful legal research assistant who specializes in extracting key information from semi-structured text.\n\nYou will be given some text which denotes a Table of Contents of some legislation. This legislation was converted from a PDF to a text file and therefore has some minor formatting errors.\n\nYou will assist a researcher by extracting some key information from the Table of Contents page into a json object, following these instructions:\n1. Extract the Title this legislation is organized under. This will almost always be near the top of the page and be in the format \"TITLE # - NAME\". Extract separately the title number and title name into variables called \"title_num\" and \"title_name\". Repeat this for the \"chapter_num\" and \"chapter_name\" as well.\n2. Determine what structure of legislation the table of contents has. The entire PDF will be organized under the title and chapter mentioned. Sections are always going to be the bottom most level of organization. Between titles/chapters and sections are some level identifiers used to group and organize sections. Depending on the table of contents, you may see \"Article\", \"Division\", or \"Part\". Take some time to understand the level identifier, which will be referred to as LEVEL. Although these level identifiers may have different names based on the specific table of contents, they all follow the same rules. Their parents are the overall title/chapter, and their children are always sections.\n3. Return the organization structure of the table of contents, extracting the follow information in json format:\norganization_structure: {\"level\": \"Part\", \"level_num\": \"II\", \"level_name\": \"MANAGEMENT\", child_sections: [{\"section_num\": 201, \"section_name\": \"Example\", \"page_number\": 3}...]}\nReminder, the LEVEL could be \"Article\", \"Division\", or \"Part\". If you see a section that doesn't have a level as a parent, still list them under a new N/A level: {\"level\": \"N/A\", \"level_num\": \"N/A\", \"level_name\": \"N/A\", child_sections: [....]}\n4. Before returning your extracted variables, check and correct minor spelling and punctuation errors.\n\nIf you get lazy and don't include the correct LEVEL, then my boss will be very angry at me. **Take your time and double check each LEVEL is correct. It is imperative we are able to fully understand the organizational structure**\n\nYour only return should be a json object. Return your variables **ONLY** in json format:\n{\"title_num\": \"\", \"title_name\": \"\", \"chapter_num\": \"\", \"chapter_name\": \"\", \"organization_structure\": {}}"
    user = f"{toc_page_text}"
    messages = util.convert_to_messages(system, user)
    #print(messages)
    params = util.get_chat_completion_params("gpt-4", messages, temperature=0.4)
    #print(params)
    completion = util.create_chat_completion(params)
    return completion


def getPromptPDFSectionExtraction(section_text, section_numbers):
    system = "You are a helpful legal research assistant who is very skilled at ready and extracting raw text from source legislation.\n\nYou will be provided with some raw source legislation, as well as a list of sections from your boss. Your job is to return the text for each requested section following these instructions:\n1. Read through and understand which Sections your boss wants you to extract the raw text for. Sections can be found by in the format: \"§402.  Interpretation. \\n The actual text of the section... \". The symbol \"§\" is used to denote a section, followed by the section number and a name.\n2. Familiarize yourself with the provided source text. Take note that at the end of the document there may be extra text that is not part of the requested sections.\n3. Read through the source text, extracting all of the text for each requested_section 4. Make sure to correct any spelling or punctuation errors found in the source text. The source text was converted from a PDF and therefore may need some minor corrections. \n\nReturn a list of these JSON objects in the following format:\n {extracted_sections:[{\"section_number\": \"\", \"section_text\": [\"\"]}]}"
    user = f"requested_sections: {json.dumps(section_numbers)}, source_text:{section_text}"
    messages = util.convert_to_messages(system, user)
    #print(messages)
    params = util.get_chat_completion_params("gpt-4-1106-preview", messages, temperature=0.4)
    completion = util.create_chat_completion(params)
    return completion

def getPromptPDFSectionExtractionSmall(target_section, source_legislation):
    system = "You are a helpful legal research assistant who is very skilled at reading and extracting raw text from source legislation.\n\nYour boss will provide you everything you need:\n1. A target_section. This is the section of legislative text that your boss wants you to extract.\n2. Source_legislation. This is some raw source legislation where the target_section is guranteed to be.\n\nYou will read through the source_legislation and extract the text of the target_section by following these instructions:\n1. Read through and understand which Section your boss wants you to extract the raw text for. Sections can be found by in the format: \"§402.  Interpretation. \\n The actual text of the section... \". The symbol \"§\" is used to denote a section, followed by the section number and a name.\n2. Familiarize yourself with the provided source text. Take note that at the beginning and end of the document there may be extra text that is not part of the requested sections.\n3. Read through the source text, extracting all of the text for the target_section.\n\n\n\nReturn the section_number and section_text in the following json format: {\"section_number\":\"\", \"section_text\": \"\"}"
    user = f"target_section: {target_section}, source_legislation:{source_legislation}"
    messages = util.convert_to_messages(system, user)
    #print(messages)
    params = util.get_chat_completion_params("gpt-3.5-turbo-1106", messages, temperature=0.4)
    completion = util.create_chat_completion(params)
    return completion

def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "mhl/",
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
        "mhl/statutes/",
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
        "mhl/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)






    

if __name__ == "__main__":
    asyncio.run(main())