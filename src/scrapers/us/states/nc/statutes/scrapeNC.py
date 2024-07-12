import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
import roman 
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from node import Node

 = "will2"
TABLE_NAME = "nc_node"
EXIT_CASES = ["aChapter", "aSubChapter", "aPart", "aSubPart", "aArticle", "aSection"]

def main():
    insert_jurisdiction_and_corpus_node()
    
    node_parent = Node("nc/statutes/", "nc/", None, "corpus", "CORPUS")
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):

            # if i < 368:
            #     continue
            url = line.strip()
            top_level_title = url.split(".html")[0].split("_")[-1]
            sql_update = f"UPDATE nc_node SET node_link = '{url}' WHERE node_top_level_title = '{top_level_title}';"
            conn = util.psql_connect("will2")
            cursor = conn.cursor()
            #sql_delete = f"DELETE FROM nc_node WHERE node_top_level_title='{top_level_title}';"
            cursor.execute(sql_update)

            conn.commit()
            cursor.close()
            conn.close()

            print(f"Top Level Title: {top_level_title}")
            print(f"URL: {url}")
            
            # scrape_per_title(url, top_level_title, node_parent)
    

def scrape_per_title(url, top_level_title, corpus_parent):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    
    soup = BeautifulSoup(data, features="html.parser")

    title_schema = ["CHAPTER", "SUBCHAPTER", "ARTICLE", "PART", "SUBPART"]
    
    parent_div = soup.find(class_="WordSection1")
    chapter_tag = parent_div.find(class_="aChapter")
    chapter_name_start = chapter_tag.get_text().strip()
    
    

    next_chapter_tag = chapter_tag.find_next_sibling()
    chapter_name_end = next_chapter_tag.get_text().strip()
    
    chapter_name = chapter_name_start + " " + chapter_name_end
    chapter_name.replace("\r", " ")
    
    chapter_number = top_level_title

    
    chapter_id = f"nc/statutes/CHAPTER={chapter_number}/"
    
    current_node = Node(chapter_id, corpus_parent, chapter_number, "structure", "CHAPTER", node_name=chapter_name)
    print(current_node.node_id)
    current_node.insert(, TABLE_NAME, "IGNORE")
    
    iterator = next_chapter_tag.find_next_sibling()

    while iterator is not None:
        element = iterator
        while element:
            if (element['class'][0] == "aBase"):
                element = element.find_next_sibling()
            else:
                break
        
        if (element is None):
            break
        new_node, return_tag = extract_structure_node(element, current_node)
        #print("  NEW NODE: ", new_node)
        
        # Handle all content nodes first
        if ("content" in new_node.node_type or new_node.node_type == "reserved"):
            iterator = return_tag
            continue
        
        currentRank = title_schema.index(current_node.node_level_classifier)
        newRank = title_schema.index(new_node.node_level_classifier)
        #print("currentRank", currentRank)
        #print("newRank", newRank)
    
                # Determine the position of the newNode in the hierarchy
        if (newRank <= currentRank):
            temp_node = current_node

            while (title_schema.index(temp_node.node_level_classifier) > newRank):
                temp_node = temp_node.node_parent
                if (temp_node.node_level_classifier == 'CHAPTER'):
                    break
                
            
            current_node = temp_node
            currentRank = title_schema.index(current_node.node_level_classifier)
            # Set the ID of the newNode and add it to the current_node's children or siblings
            if (newRank == currentRank):
                if (not current_node.node_parent):
                    print("current_node.parent undefined!")
                    exit(1)

                node_num = new_node.node_name.split(" ")[1].strip()
                if node_num[-1] == ".":
                    node_num = node_num[:-1]
                new_node.node_parent = current_node.node_parent
                new_node.reset_id(node_num)
                
                
                
                
                current_node = new_node
            else:
                node_num = new_node.node_name.split(" ")[1].strip()
                if node_num[-1] == ".":
                    node_num = node_num[:-1]
                new_node.parent = current_node
                new_node.reset_id(node_num)
                
                current_node = new_node
            
        else:
            # Set the ID of the newNode and add it to the current_node's children
            node_num = new_node.node_name.split(" ")[1].strip()
            if node_num[-1] == ".":
                node_num = node_num[:-1]
            new_node.reset_id(node_num)
            
            new_node.parent = current_node
            current_node = new_node
        #print(current_node.node_id)
        unique_insert = current_node.insert(, TABLE_NAME, "IGNORE")
        if (not unique_insert):
            print("Ignored!")
            row = util.read_row_by_node_id(, TABLE_NAME, current_node.node_id)   
            print(row)
            if row[0][6] == new_node.node_name:
                #print("Adding to previous node!")
                pass
            else:
                #### FIX THIS LATER
                pass
                #exit(1)

        iterator = return_tag
        
           



       
def extract_structure_node(tag, node_parent):
    tag_name = tag['class'][0]
    if tag.get_text().strip() == "":
        tag = tag.find_next_sibling()
        tag_name = tag['class'][0]
        

    next_tag = tag.find_next_sibling()     
    next_tag_name = next_tag['class'][0]
    top_level_title = node_parent.node_top_level_title
    

    
    if tag_name in next_tag_name:
        # Two tags for one structure node
        node_name_start = tag.get_text().strip()

        node_number = node_name_start.split(" ")[1].strip()
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        node_level_classifier = node_name_start.split(" ")[0].upper()
        node_name_end = next_tag.get_text().strip()
        node_name = node_name_start + " " + node_name_end
        if next_tag.find_next_sibling()['class'][0] == next_tag_name:
            return_tag = next_tag.find_next_sibling().find_next_sibling()
        else:
            return_tag = next_tag.find_next_sibling()


        
                    

        
    else:
        node_name = tag.get_text().strip()
        node_number = node_name.split(" ")[1].strip()
        if node_number[-1] == ".":
            node_number = node_number[:-1]
        node_level_classifier = node_name.split(" ")[0].upper()
        return_tag = next_tag


    if ("Reserved" in node_name or "Expired " in node_name or "Not in effect" in node_name or  "articles " in node_name.lower() or "subchapters " in node_name.lower()  or "subparts " in node_name.lower()) and "§" not in node_name:
        node_type = "reserved"
        
        if node_level_classifier[:-1] == "s":
            node_level_classifier = node_level_classifier[:-1]
            node_numbers = node_name.split(" ")
            new_node_number = ""
            for i in range(1, len(node_numbers)):
                new_node_number += node_numbers[i] + "-"
            new_node_number = "[" + new_node_number[:-1] + "]"
            node_number = new_node_number
        else:
            node_level_classifier = "SECTION"
            node_number = node_number.split("-")[-1]
            node_number = node_number.replace(":", "")
            node_number = "[" + node_number + "]"
                
        node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
        if node_level_classifier == "SECTION":
            node_id = node_id[:-1]

        reserved_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_name=node_name)
        reserved_node.insert(, TABLE_NAME, "FORCE-NEW-VERSION")
        print(reserved_node.node_id)
        return reserved_node, return_tag

    

    if "Section" not in tag_name: #) and not ("Article" in tag_name and could_convert):
        node_type = "structure"
        node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}/"
        structure_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_name=node_name)
        return structure_node, return_tag
    
    node_type = "content"
    node_level_classifier = "SECTION"
    node_number = node_number.split("-")[-1]
    if node_number[:-1] == ".":
        node_number = node_number[:-1]
    node_id = f"{node_parent.node_id}{node_level_classifier}={node_number}"
    
    node_citation = f"N.C.G.S. § {top_level_title}-{node_number}"
    node_addendum = ""
    node_text = []
    if "Repealed" in node_name or "Reserved for" in node_name or "Expired " in node_name or "Not in effect" in node_name:
        node_type = "reserved"
        
        
        
        

    # Find all <p> tags which belong to the Section
    iterator = next_tag
    while iterator:
        
        iterator_tag_name = iterator['class'][0]
       # print(iterator_tag_name)
        if (iterator_tag_name in EXIT_CASES):

            
            try:
                temp = iterator.get_text().strip()
                #print(temp)
                if temp == "":
                    iterator = iterator.find_next_sibling()
                    continue
                level = temp.split(" ")[0].strip()
                if level.upper() not in ["CHAPTER", "SUBCHAPTER", "ARTICLE", "PART", "SUBPART", "SECTION"]:
                    break
                if (level.upper() != "ARTICLE"):
                    break
                node_num = temp.split(" ")[1].strip()
                node_num = node_num.replace(".", "")
                roman_numeral = roman.fromRoman(node_num)
                #print("Roman numeral: ", roman_numeral)
            except:
                #print("GET ME OUTTA HERE!")
                break 

        if (iterator.find(class_="cHistoryNote")):
            node_addendum_tag = iterator.find(class_="cHistoryNote")
            node_addendum = node_addendum_tag.get_text().strip()
            node_addendum_tag.string = ""
        
        txt = iterator.get_text().strip()
        if txt != "":
            node_text.append(txt)
        iterator = iterator.find_next_sibling()
    
    content_node = Node(node_id, node_parent, top_level_title, node_type, node_level_classifier, node_name=node_name, node_text=node_text, node_citation=node_citation, node_addendum=node_addendum)
    content_node.insert(, TABLE_NAME, "FORCE-NEW-VERSION")
    print(content_node.node_id)
    return content_node, iterator

        
        



        
        






def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "nc/",
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
        "nc/statutes/",
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
        "nc/",
        None,
        None,
        None,
        None,
        None,
    )
    insert_node_ignore_duplicate(jurisdiction_row_data)
    insert_node_ignore_duplicate(corpus_row_data)







if __name__ == "__main__":
    main()