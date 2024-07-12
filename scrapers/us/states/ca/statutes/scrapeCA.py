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
from typing import List, Dict, Any
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
from pydanticModels import Node, NodeID
import utilityFunctions as util
from scrapingHelpers import insert_jurisdiction_and_corpus_node, insert_node_ignore_duplicate, insert_node


BASE_URL = 'https://leginfo.legislature.ca.gov/'
ROOT_URL = "https://leginfo.legislature.ca.gov/faces/codes.xhtml"
COUNTRY = "us"
JURISDICTION="ca"
CORPUS="statutes"
TABLE_NAME=f"{COUNTRY}_{JURISDICTION}_{CORPUS}"

def main():
    corpus_node: Node = insert_jurisdiction_and_corpus_node(COUNTRY, JURISDICTION, CORPUS)
    scrape(corpus_node)

all_codes = [("BPC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=BPC" ),("CIV","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CIV" ),("CCP","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CCP" ),("COM","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=COM" ),("CORP","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CORP" ),("EDC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=EDC" ),("ELEC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=ELEC" ),("EVID","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=EVID" ),("FAM","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FAM" ),("FIN","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FIN" ),("FGC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FGC" ),("FAC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=FAC" ),("GOV","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=GOV" ),("HNC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=HNC" ),("HSC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=HSC" ),("INS","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=INS" ),("LAB","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=LAB" ),("MVC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=MVC" ),("PEN","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PEN" ),("PROB","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PROB" ),("PCC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PCC" ),("PRC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PRC" ),("PUC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=PUC" ),("RTC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=RTC" ),("SHC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=SHC" ),("UIC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=UIC" ),("VEH","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=VEH" ),("WAT","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=WAT" ),("WIC","https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=WIC" )]

# Current 
# class=treecodetitle
def scrape(corpus: Node):
    DIVISION = ["DIVISION", "PART", "TITLE", "CHAPTER", "ARTICLE"]
    PART = ["PART", "TITLE", "DIVISION", "CHAPTER", "ARTICLE"]
    TITLE = ["TITLE", "DIVISION", "PART", "CHAPTER", "ARTICLE"]
    SHORT = ["DIVISION", "CHAPTER", "ARTICLE"]
    REGULAR = ["DIVISION", "PART", "CHAPTER", "ARTICLE"]
    BASE = ["ca", "statutes", "code"]

    DIVISION_CODE = ["WAT", "CIV"]
    PART_CODE = ["CCP", 'PEN']
    TITLE_CODE = ["GOV", "CORP", "EDC"]
    SHORT_CODE = ["VEH", "COM", "FIN", "EVID"]
    
    
    
    skip = True
    for i, code_tup in enumerate(all_codes):
        if(code_tup[0] == "WAT"):
            skip = False
        if skip:
            continue
        
        
        
        code: str = code_tup[0]
        url = code_tup[1]
        print(f"Scraping for code: {code}")
        title_schema = []

        if (code in DIVISION_CODE):
            title_schema = DIVISION
        elif (code in PART_CODE):
            title_schema = PART
        elif (code in TITLE_CODE):
            title_schema = TITLE
        elif (code in SHORT_CODE):
            title_schema = SHORT
        else:
            title_schema = REGULAR
        title_schema = BASE + title_schema

        code_model = Node(f"{COUNTRY}/{JURISDICTION}/{CORPUS}/code={code.lower()}", parent=corpus.node_id, top_level_title=code.lower(), node_type="structure", level_classifier="code", node_link=url )
        util.pydantic_insert(TABLE_NAME, [code_model])

        scrape_structure_nodes(url, title_schema, code_model, code)
        
# For every root node, scrape all structure nodes, getting a list of all valid HTML div elements which have content node children
def scrape_structure_nodes(url: str, title_schema: List[str], node_parent: Node, top_level_title: str):
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
    # Find the name of the code we're scraping
    
    # Find the HTML container for actual content
    codesbrchfrm = soup.find(id="codesbrchfrm")
    if (not codesbrchfrm):
        print("Couldn't find codesbrchform!")
        exit(1)
    
    branchChildren = codesbrchfrm.find_all(recursive=False)
    
    container = branchChildren[4].contents[0]
    
    if (not container):
        print("code container undefined!")
        exit(1)

    div_elements = []
    # vFind all div_elements in container
    for i, current_element in enumerate(container.find_all(recursive=False)):
        
        # Format Div
        if (i % 2 == 1):
            continue
        
        div_elements.append(current_element)
        
    
    scrape_per_title(div_elements, title_schema, node_parent, top_level_title)
    return node_parent


def scrape_per_title(structure_divs, title_schema: List[str], node_parent: Node, top_level_title: str):
    current_node = node_parent
    # Find the container
    

    for i, div in enumerate(structure_divs):
        # Skip useless style divs
        new_node = get_structure_node_attributes(div, top_level_title, current_node, title_schema)
        
        
        # Check if node level classifier is in title schema
        
        
        
        
        if ("reserved" in new_node.node_name):
            continue

        if(new_node.node_type == "description" or new_node.node_type == "reference"):
            new_name = new_node.node_name.replace(" ","_")
            new_node.node_id = current_node.node_id + new_node.node_level_classifier + "=" + new_name + "/"
            new_node.node_parent = node_parent
            print(new_node)
            new_node.insert(TABLE_NAME)
            
            scrape_content_node(new_node, top_level_title)
            continue
        
        elif (new_node.node_level_classifier not in title_schema):
            index = title_schema.index(new_node.node_parent.node_level_classifier) + 1
            if(index == len(title_schema)):
                if ("codes_displayText" in new_node.node_link):
                    new_node.node_level_classifier = "SECTION"
                else:
                    new_node.node_level_classifier = "SUB" + new_node.node_parent.node_level_classifier
            else:
                new_node.node_level_classifier = title_schema[index]
            
           
        
        if (new_node.node_level_classifier in title_schema):
            # Actually build node
            # POSSIBLY ADD

            currentRank = title_schema.index(current_node.node_level_classifier)
            newRank = title_schema.index(new_node.node_level_classifier)

            # Determine the position of the newNode in the hierarchy
            if (newRank <= currentRank):
                temp_node = current_node

                while (title_schema.index(temp_node.node_level_classifier) > newRank):
                    temp_node = temp_node.node_parent
                    if (temp_node.node_level_classifier == 'code'):
                        break
                    
                
                current_node = temp_node
                currentRank = title_schema.index(current_node.node_level_classifier)
                # Set the ID of the newNode and add it to the current_node's children or siblings
                if (newRank == currentRank):
                    if (not current_node.node_parent):
                        print("current_node.parent undefined!")
                        exit(1)

                    new_node.node_id = current_node.node_parent.node_id + new_node.node_level_classifier + "=" + new_node.node_name.split(" ")[1] + "/"
                    if(new_node.node_type == "reference"):
                        new_node.node_name = new_node.node_name.split(" ")[1]
                        new_node.node_name = new_node.node_name.replace("_","")
                    
                    new_node.node_parent = current_node.node_parent
                    
                    current_node = new_node
                else:
                    new_node.node_id = temp_node.node_id + new_node.node_level_classifier + "=" + new_node.node_name.split(" ")[1]+ "/"
                    if(new_node.node_type == "reference"):
                        new_node.node_name = new_node.node_name.split(" ")[1]
                        new_node.node_name = new_node.node_name.replace("_","")
                    
                    new_node.parent = current_node
                    current_node = new_node
                
            else:
                # Set the ID of the newNode and add it to the current_node's children
                new_node.node_id += new_node.node_level_classifier + "=" + new_node.node_name.split(" ")[1] + "/"
                if(new_node.node_type == "reference"):
                        new_node.node_name = new_node.node_name.split(" ")[1]
                        new_node.node_name = new_node.node_name.replace("_"," ")
                #new_node.node_id = new_node.node_id.replace("./", "/")
                
                new_node.parent = current_node
                current_node = new_node
            

            # Print the current_node and scrape content if necessary
            current_node.node_id = current_node.node_id.replace("./", "/")
            print(current_node)
            for i in range(2, 10):
                try:
                    current_node.insert(TABLE_NAME)
                    break
                except:
                    # Remove all characters from row_data.node_id after "-version"
                    temp = current_node.node_id
                    if("-version" in current_node.node_id):
                        temp = current_node.node_id.split("-version")[0]

                    current_node.node_id = temp + f"-version_{i}"
            
            #print(current_node)
            if ("codes_displayText" in  new_node.node_link and new_node.node_type != "reserved"):
                #print(f"Scraping all content for {new_node.node_id}")
                scrape_content_node(new_node, top_level_title)
        elif ("codes_displayText" in  new_node.node_link  and new_node.node_type != "reserved" and new_node.node_type != "description"):
                
                #print(f"Scraping all content for {new_node.node_id}")
                new_node.node_id += new_node.node_level_classifier + "=" + new_node.node_name.split(" ")[1] + "/"
                new_node.node_parent = current_node
                print(new_node)
                for i in range(2, 10):
                    try:
                        new_node.insert(TABLE_NAME)
                        break
                    except:
                        # Remove all characters from row_data.node_id after "-version"
                        temp = new_node.node_id
                        if("-version" in new_node.node_id):
                            temp = new_node.node_id.split("-version")[0]

                        new_node.node_id = temp + f"-version_{i}"
                scrape_content_node(new_node, top_level_title)
        else:
            print("WEIRD CASE!")
            new_name = new_node.node_name.replace(" ","_")
            new_node.node_id = current_node.node_id + new_node.node_level_classifier + "=" + new_name + "/"
            new_node.node_parent = node_parent
            new_node.node_id = new_node.node_id.replace("./", "/")
            print(new_node)
            for i in range(2, 10):
                try:
                    new_node.insert(TABLE_NAME)
                    break
                except:
                    # Remove all characters from row_data.node_id after "-version"
                    temp = new_node.node_id
                    if("-version" in new_node.node_id):
                        temp = new_node.node_id.split("-version")[0]

                    new_node.node_id = temp + f"-version_{i}"
            
            #print(current_node)
            if ("codes_displayText" in  new_node.node_link and new_node.node_type != "reserved"):
                #print(f"Scraping all content for {new_node.node_id}")
                scrape_content_node(new_node, top_level_title)
            
    


    

def get_structure_node_attributes(current_element, top_level_title: str, node_parent: Node, title_schema: List[str]):
    # Find the "a" tag inside the current_element
    #print(current_element.name)
    a_tag = current_element.find("a")

    # Ensure the a_tag is found
    if (not a_tag):
        print("No 'a' tag found in the current element.")
        exit(1)
    # Extract href value
    link = BASE_URL + a_tag["href"]
    if (link is None):
        print("Invalid link!")
        exit(1)
    
    # Assume the first child element of a_tag contains the title and name
    node_name: str = a_tag.contents[0].get_text().strip()
    if (not node_name):
        print("No first child element with text found in the 'a' tag.")
        exit(1)
    
    
    # Get content from the second child element of a_tag
    node_tags = None



    title_classifier = node_name.split(" ")[0]
    title_classifier = title_classifier.replace("[", "")
    node_level_classifier = title_classifier.replace("]", "")

    try:
        temp = node_name.split(" ")[1]
        if(temp[-1] == "."):
            temp = temp[:-1]
        node_type = "structure"
        chapter_number = int(temp[0])
        
    except:
        if (node_parent.level_classifier == "code"):
            node_type = "reference"
            node_level_classifier = title_schema[3]
            


    node_link = link
    # Node graph traversal stuff
    node_id = node_parent.node_id
    
    row_data = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier=node_level_classifier, node_name=node_name, node_link=node_link, node_tags=node_tags)
    return row_data
    
    

def scrape_content_node(scraping_node: Node, top_level_title: str):

    url = scraping_node.link
    
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
    
   

    container = soup.find(id="manylawsections")
    if (not container):
        print("manylawsections container not found!")
        print(url)
        return

    divCon = container.contents[-1]
    if (not divCon):
        print("divCon element cannot be found!")
        exit(1)


    fontContainer = divCon.contents[0]
    if (not fontContainer):
        print("font element cannot be found!")
        exit(1)

    section_divs = fontContainer.find_all("div", recursive=False)
    
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=BPC&sectionNum=Section 115.
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=BPC&sectionNum=115.
    # https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=1358.1.
    
    for i, div in enumerate(section_divs):
        if i == 0:
            continue
        #print(div)
        # find first child div element and extract the .textContent
        try:
            section_container = div.find("a")
            node_name = section_container.get_text().strip()
            citation = f"Cal. {top_level_title} § {node_name}"
            level_classifier = "section"
            node_id = scraping_node.node_id + level_classifier + "=" + node_name
            link = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode={top_level_title}&sectionNum={node_name}"
            node_name = "Section " + node_name
            node_type = "content"
            node_text = []
        except:
            continue
        
        
        print(f"{node_name},",end="")
        
        for i, p_tag in enumerate(div.find_all(recursive=True)):
            if i <= 1 or p_tag.name == "i":
                continue
            
            text_to_add = p_tag.get_text().strip()
            if(text_to_add == ""):
                continue
            #if len(node_text)==0:
                #text_to_add = node_name + " " + text_to_add
            
            node_text.append(text_to_add)

        node_addendum = node_text.pop()
        row_data = Node(id=node_id, parent=scraping_node.node_id, top_level_title=top_level_title, node_type=node_type, level_classifier=level_classifier, node_name=node_name, link=link, node_text=node_text, addendum=node_addendum, citation=citation)

        for i in range(2, 10):
            try:
                row_data.insert(TABLE_NAME)
                break
            except:
                # Remove all characters from row_data.node_id after "-version"
                temp = row_data.node_id
                if("-version" in row_data.node_id):
                    temp = row_data.node_id.split("-version")[0]

                row_data.node_id = temp + f"-version_{i}"
                row_data.node_type = "duplicate"
                
        

    
    # get_nested_content_nodes(div_elements, scraping_node, top_level_title)
    print()
    return

def get_nested_content_nodes(div_elements, parent_node, top_level_title):
    exit(1)
    # sectionIds = {}
    # # Make new set of strings called all_ids
    # all_ids = set()

    # # Loop through all div elements, to find 1 content node and all sub_content_nodes
    # for (const div of div_elements) {
    #     //console.log(div.outerHTML)
    #     const header = div.querySelector('h6');
    #     //console.log(header.outerHTML)
    #     if (!header) continue;
        
    #     let sectionId = parent_node.id + `/SECTION=${(header.textContent?.trim())?.slice(0,-1) || ''}`
    #     if (sectionIds[sectionId]) {
    #         let toAdd = `&bis=${sectionIds[sectionId]}`;
    #         sectionIds[sectionId] += 1;
    #         sectionId += toAdd;
    #     } else {
    #         sectionIds[sectionId] = 1;
    #     }

    #     // Create the content node
    #     const content_node: scraping_node = create_new_scraping_node(
    #         sectionId,
    #         "content_node",
    #         (header.textContent?.trim() || '').slice(0,-1),
    #         'SECTION',
    #         SECTION_CITATION_FORMAT.join(rootCode) + (header.textContent?.trim() || '').slice(0, -1),
    #         parent_node.depth + 1,
    #         BASE_URL + header.querySelector('a')?.getAttribute('href'),
    #         parent_node.id,
    #         [],
    #     );
        
    #     // Create dictionary of unique ids
    #     const usedIds: {[key: string]: number} = {};
    #     content_node.link = `https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=${rootCode}&sectionNum=${content_node.title}.`;
    #     content_node.node_type = "content_node";
    #     parent_node.children.push(content_node);
    #     parent_node.children_nodes.push(content_node.id);
    #     content_node.has_direct_child_content_nodes = true;
    #     let current_node = content_node;

    #     // Loop through all children of the div element, to find all sub_content_nodes
    #     for (const child of Array.from(div.children)) {
    #         // Skip any children that are not <p> tags, or poorly formatted <p> tags
    #         if (child.tagName === 'h6' || child.textContent?.trim() === "") {
    #             continue;
    #             // If we find a valid <p> tag, create a sub_content_node
    #         } else if (child.tagName === 'P' && child.textContent?.trim()) {
    #             // Create a base node with common attributes of all cases
    #             const textContent = child.textContent?.trim() || '';
    #             let base_node: scraping_node = create_new_scraping_node(
    #                 '',
    #                 'sub_content_node',
    #                 '',
    #                 'SUB_SECTION',
    #                 current_node.citation?.split("/").pop() || '',
    #                 current_node.depth + 1,
    #                 content_node.link,
    #                 current_node.id,
    #                 [],
    #                 textContent,
    #                 0,
    #                 [],
    #                 [],
    #                 [],
    #             );
    #             base_node.node_type = "sub_content_node";
                
    #             // Find the margin of the <p> tag, which will determine the depth of the sub_content_node relative to the section node
    #             const marginToDepthMap: { [key: string]: number; } = {
    #                 "0px": 1,
    #                 "1em": 2,
    #                 "2.5em": 3,
    #                 "4em": 4,
    #                 "5.5em": 5,
    #                 "7em": 6,
    #                 "8.5em": 7,
    #                 "10em": 8
    #             };
    #             const margin = (child as HTMLElement).style?.marginLeft || '0px';
    #             const depth: number = marginToDepthMap[margin] + content_node.depth;
    #             //console.log(textContent)
    #             //console.log(`margin: ${margin}, depth: ${depth}, current_node.depth: ${current_node.depth}`)
    #             // Determine the depth of margin, and therefore the depth of the sub_content_node. Either add the sub_content_node to the tree as a child, or climb up the tree to find the correct parent node
    #             if (depth > current_node.depth) {
    #                 // The current node is a direct child of the last node
    #             } else if (depth === current_node.depth) {
    #                 // The current node is a sibling of the last node
    #                 current_node = current_node.parent || parent_node;
    #             } else {
    #                 // We've climbed back up the hierarchy
    #                 while (depth <= current_node.depth) {
    #                     //console.log(current_node.id)
    #                     current_node = current_node.parent || parent_node;
    #                 }
    #                 //console.log(current_node.id)
    #             }
    #             // Update the base node with common attributes
    #             const [external_citations, internal_citations] = extractCitations(textContent, rootCode);
    #             base_node.external_references = external_citations;
    #             base_node.internal_references = internal_citations;
    #             base_node.sub_text = textContent;
    #             base_node.sub_text_tokens = await tokens_from_string(base_node.sub_text);

    #             // Check for the case where the sub_content_node contains 0, 1 or 2 titles
    #             let hasAddendum = false;
                
    #             let sub_content_titles = getStartingElements(textContent);
    #             if(textContent.includes("Stats.")&& textContent[0] === "(") {
    #                 hasAddendum = true;
    #                 base_node.node_type = "addendum_node";
    #                 sub_content_titles = [];
    #             }
                
            
    #             // Single node case which has 0 or 1 title. Therefore must live right under the content node
    #             if (sub_content_titles.length === 0 || sub_content_titles.length === 1) {

    #                 // update base_node with information for the single node
    #                 base_node.title = sub_content_titles[0] || '';
    #                 base_node.depth = current_node.depth + 1;

    #                 if (hasAddendum) {
    #                     // Update base_node to indicate that it is an addendum
    #                     base_node.title = 'Addendum';
    #                     base_node.node_level_classifier = 'Addendum';
    #                 }
                    
    #             // Multi node case. Create a new node for the first "placeholder" title, then update base_node with information for the second node
    #             } else {
    #                 for (let i = 0; i < sub_content_titles.length-1; i++) {
    #                     const node: scraping_node = create_new_scraping_node(
    #                         `${current_node.id}/${sub_content_titles[i]}`,
    #                         'sub_content_node',
    #                         sub_content_titles[i],
    #                         'sub_section',
    #                         current_node.citation + "/" + sub_content_titles[i],
    #                         current_node.depth + 1,
    #                         content_node.link,
    #                         current_node.id,
    #                         [],
    #                         '',
    #                         0,
    #                         [],
    #                         [],
    #                         [],
    #                     );
    #                     node.node_type = "sub_content_node";
    #                     node.parent = current_node;
    #                     node.parent_node = current_node.id;
    #                     node.parent_section = content_node.id;
    #                     current_node.children.push(node);
    #                     current_node.children_nodes.push(node.id);
    #                     current_node = node;
    #                 }
                    
    #                 base_node.title = sub_content_titles[1];
    #                 base_node.depth = current_node.depth + 1;
    #             }
    #             // Always add the base node to the tree
                
    #             base_node.parent_section = content_node.id;
    #             base_node.parent = current_node;
    #             base_node.parent_node = current_node.id;
    #             base_node.citation = `${current_node.citation}${base_node.title.trim()}`;
    #             let newId = `${current_node.id}/${base_node.title.trim()}`;
    #             // Avoid duplicate IDs for a subsection of a content node
    #             // Works with (a) and ''
    #             if (usedIds[newId] && !hasAddendum) {
    #                 let toReplace = "";
    #                 let lastSlash = 0;
    #                 if(base_node.title.trim() === '') {
    #                     toReplace = `&p=${usedIds[newId]}`;
    #                     lastSlash = 1;
    #                 } else {
    #                     toReplace = base_node.title + `&p=${usedIds[newId]}`;
    #                 }
    #                 base_node.title = toReplace;
    #                 base_node.citation  += `(p=${usedIds[newId]})`;
    #                 usedIds[newId] += 1;
    #                 // find index of last "/" in newId
    #                 lastSlash += newId.lastIndexOf("/");
                    
    #                 // Replace the last instance of "/p=" with "/p=1"
    #                 newId = newId.slice(0, lastSlash) + toReplace;
    #             } else {
    #                 usedIds[newId] = 1;
    #             }
    #             base_node.id = newId;
    #             current_node.children.push(base_node);
    #             current_node.children_nodes.push(base_node.id)
    #             current_node = base_node;
                
    #         }
    #     }
    #     let nodes_added = content_node.children_nodes.length + 1;
    #     //console.log(`  - Added ${nodes_added} nodes...`)
    #     TOTAL_NODE_COUNT += nodes_added;
    
    



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




if __name__ == "__main__":
    main()