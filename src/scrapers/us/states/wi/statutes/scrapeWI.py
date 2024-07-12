import json
import re
import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

 = "madeline"
TABLE_NAME = "wi_node"
BASE_URL = "https://docs.legis.wisconsin.gov/statutes/statutes/"
TOC_URL = "URL to main page which contains all top_level_title links"
SKIP_TITLE = 32 # If you want to skip the first n titles, set this to n

def main():
    insert_jurisdiction_and_corpus_node()
    with open(f"{DIR}/data/top_level_titles.txt","r") as read_file:
        for i, line in enumerate(read_file):
            if i < SKIP_TITLE:
                continue
            url = line.strip()
            scrape_per_title(url)
    

def scrape_per_title(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    print(url)
    chapter_container = soup.find("div", class_="statutes")
    chapter_number_get = chapter_container.find("div", class_="qs_num_chapnum_").get_text()
    chapter_name_get = chapter_container.find("div", class_="qs_title_chapter_").get_text()
    chapter_number = chapter_number_get.split(" ")[-1].replace("\n", "")
    chapter_name = f"{chapter_number_get} {chapter_name_get}"
    node_type = "structure"
    node_level_classifier = "CHAPTER"
    print(chapter_number)
    node_id = f"wi/statutes/CHAPTER={chapter_number}/"
    node_link = url
    target_element = soup.find(class_="qs_atxt_1section_ level3")

# Find the addendum and reference elements
    node_addendum_find = chapter_container.find("div", class_="qs_note_note_")
    node_references_find = chapter_container.find("div", class_="qs_note_xref_")
    node_addendum = None
    node_references = None

# Check if the elements occur before the target element
# This is done by checking if they are found in the HTML before the target element
    addendum_before = node_addendum_find and target_element and (str(soup).find(str(node_addendum_find)) < str(soup).find(str(target_element)))
    references_before = node_references_find and target_element and (str(soup).find(str(node_references_find)) < str(soup).find(str(target_element)))

# Extract text if the nodes exist
    node_addendum_text = node_addendum_find.get_text().strip().replace('\n', ' ') if addendum_before else None
    node_references_text = node_references_find.get_text().strip().replace('\n', ' ')  if references_before else None
    if node_addendum_text is not None:
        node_addendum = node_addendum_text
        
    if node_references_text is not None:
        node_references= node_references_text
        node_references = json.dumps(node_references)
    chapter_node_data = (node_id, chapter_number, node_type, node_level_classifier, None, None, None, node_link, node_addendum, chapter_name, None, None, None, None, None, "wi/statutes/", None, None, node_references, None, None)
    insert_node_ignore_duplicate(chapter_node_data)


    node_parent = node_id
    top_level_title = chapter_number

    subchapter_check = chapter_container.find("div", class_="qs_toc_subchap_")
    if subchapter_check is not None and top_level_title == "35":
        subchapters = chapter_container.find_all('div', class_='qs_toc_subchap_')
        print(subchapters)


        for index, subchapter in enumerate(subchapters):
            
            # Assuming that each subchapter name follows its number
            subchapter_name = subchapter.get_text(strip=True)
            print(subchapter_name)
            if ("SUBCHAPTER" in subchapter_name):
                subchapter_counter = 1 
                subchapter_number_text = subchapter_name
                subchapter_name = subchapters[index + 1]
                subchapter_name_text = subchapter_name.get_text(strip=True)
                subchapter_full_text = f"{subchapter_number_text} {subchapter_name_text}"

                node_type = "structure"
                node_level_classifier = "SUBCHAPTER"
                subchapter_number = subchapter_number_text.split("SUBCHAPTER ")[-1]
                node_id = f"{node_parent}SUBCHAPTER={subchapter_number}/"
                node_link = url
                node_addendum = None
                node_references = None
                node_name = subchapter_full_text
                node_data = (node_id, chapter_number, node_type, node_level_classifier, None, None, None, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, None)
                insert_node_ignore_duplicate(node_data)
                subchapter_node_parent = node_id
                subchapter_lower = subchapter_number.lower()
                sub_chapter_number_next = subchapter_number


                entries = []
                next_element = subchapter_name.find_next_sibling()
                while next_element and next_element.name == 'div' and 'qs_toc_entry_' in next_element.get('class', []):
                    entries.append(next_element)
                    next_element = next_element.find_next_sibling()
                    if next_element and 'qs_toc_subchap_' in next_element.get('class', []):
                        break
                for entry in entries:
                    entry_text = entry.get_text()
                    section_number = entry_text.split()
                    section_number = section_number[0]
                    section_url = ""
                    section_url = url + "/" + subchapter_lower + "/" + section_number.split(".")[-1]
                    print(section_url)

                    scrape_subchapter_sections(section_url, top_level_title, subchapter_node_parent, entry_text)

            elif ("SUBCHAPTER" not in subchapter_name):
                subchapter_name_text = subchapter_name
                subchapter_full_text = f"{subchapter_number_text} {subchapter_name_text}"


                node_type = "structure"
                node_level_classifier = "SUBCHAPTER"
                node_id = f"{node_parent}SUBCHAPTER={sub_chapter_number_next}.{subchapter_counter}/"
                node_link = url
                node_addendum = None
                node_references = None
                node_name = subchapter_full_text
                node_data = (node_id, chapter_number, node_type, node_level_classifier, None, None, None, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, None)
                insert_node_ignore_duplicate(node_data)
                subchapter_node_parent = node_id
                subchapter_lower = subchapter_number.lower()
                subchapter_counter += 1

                entries = []
                next_element = subchapter.find_next_sibling()
                while next_element and next_element.name == 'div' and 'qs_toc_entry_' in next_element.get('class', []):
                    entries.append(next_element)
                    next_element = next_element.find_next_sibling()
                    if next_element and 'qs_toc_subchap_' in next_element.get('class', []):
                        break
                for entry in entries:
                    entry_text = entry.get_text()
                    section_number = entry_text.split()
                    section_number = section_number[0]
                    section_url = ""
                    section_url = url + "/" + subchapter_lower + "/" + section_number.split(".")[-1]
                    print(section_url)

                    scrape_subchapter_sections(section_url, top_level_title, subchapter_node_parent, entry_text)




    elif subchapter_check is not None:
        subchapters = chapter_container.find_all('div', class_='qs_toc_subchap_')


        for index, subchapter in enumerate(subchapters):
            
            # Assuming that each subchapter name follows its number
            if index % 2 == 0:  # subchapter number
                subchapter_number_text = subchapter.get_text(strip=True)
                subchapter_name = subchapters[index + 1]  # subchapter name
                subchapter_name_text = subchapter_name.get_text(strip=True)
          
                
                subchapter_full_text = f"{subchapter_number_text} {subchapter_name_text}"
                print(f"Full Subchapter Text: {subchapter_full_text}")


                node_type = "structure"
                node_level_classifier = "SUBCHAPTER"
                subchapter_number = subchapter_number_text.split("SUBCHAPTER ")[-1]
                node_id = f"{node_parent}SUBCHAPTER={subchapter_number}/"
                node_link = url
                node_addendum = None
                node_references = None
                node_name = subchapter_full_text
                node_data = (node_id, chapter_number, node_type, node_level_classifier, None, None, None, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, None)
                insert_node_ignore_duplicate(node_data)
                subchapter_node_parent = node_id
                subchapter_lower = subchapter_number.lower()

                entries = []
                next_element = subchapter_name.find_next_sibling()
                while next_element and next_element.name == 'div' and 'qs_toc_entry_' in next_element.get('class', []):
                    entries.append(next_element)
                    next_element = next_element.find_next_sibling()
                    if next_element and 'qs_toc_subchap_' in next_element.get('class', []):
            
                        break
                for entry in entries:
                    entry_text = entry.get_text()
                    print(f"Entry: {entry_text}")
                    section_number = entry_text.split()
                    section_number = section_number[0]
                    print(section_number)
                    section_url = ""
                    section_url = url + "/" + subchapter_lower + "/" + section_number.split(".")[-1]
                    print(section_url)

                    scrape_subchapter_sections(section_url, top_level_title, subchapter_node_parent, entry_text)
            
        
    else:
        section_links = chapter_container.find_all("div", class_="qs_toc_entry_")
        for section in section_links:
            
            section_number = section.find("a").get_text()
            url = node_link + "/" + section_number.split(".")[-1]
            response = urllib.request.urlopen(url)
            data = response.read()      
            text = data.decode('utf-8', 'ignore')  
            soup = BeautifulSoup(text, features="html.parser")
            node_id = f"{node_parent}SECTION={section_number}"
            print(url)
        
            data_section_value = section_number
            print(data_section_value)
            
            node_text = []
            node_tags = {}
            node_addendum = None
            node_type = "content"
            node_level_classifier = "SECTION"
            node_name = None
         
            get_all_sections_container = soup.find_all("div", attrs={"data-section": data_section_value})

            for section_value in get_all_sections_container:
            
                first_a_tag = section_value.find("a", class_="reference")

                if first_a_tag:
                    first_a_tag.decompose()

                reference_check = section_value.find("span", class_="reference") 
                section_text = section_value.get_text().strip().replace('\n', ' ').encode('ascii', 'ignore').decode('ascii')

            
                history_check = section_value.find("span", class_="qs_note_history_")

                if ("History:" in section_text): 
                    node_addendum = section_text
                    node_addendum_pretty = node_addendum.split()
                    node_addendum = " ".join(node_addendum_pretty[2:])

                elif ("Cross-reference" in section_text and reference_check is not None):
                    node_tags["Cross-reference"] = section_text

                elif ("Annotation" in section_text):
                    node_tags["Annotation"] = section_text

                elif ("NOTE:" in section_text):
                    node_tags["Note"] = section_text

                else:
                    node_text.append(section_text)
        
   
            node_name_pattern = r"(\d+\.\d+)\s+(.*?\.)"
            print(node_text)
            print(node_text[0])
            match = re.search(node_name_pattern, node_text[0])
            # match = re.search(node_name_pattern, node_text[0])

            if match:
                node_name = f"{match.group(1)} {match.group(2)}"
                print(node_name)

            node_name = f"Section {node_name}"
            node_tags = json.dumps(node_tags)
            node_citation = f"Wis. Stat. § {section_number}"

            node_data = (node_id, chapter_number, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
            insert_node_ignore_duplicate(node_data)



def scrape_subchapter_sections(url, top_level_title, node_parent, entry_text):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8', 'ignore') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")
    entry_text = entry_text
    section_number = entry_text.split()
    section_number = section_number[0]
    node_id = f"{node_parent}SECTION={section_number}"

    data_section_value = section_number
    node_text = []
    node_tags = {}
    node_link = url
    node_addendum = None
    node_type = "content"
    node_level_classifier = "SECTION"
    node_name = None
    print(data_section_value)

    get_all_sections_container = soup.find_all("div", attrs={"data-section": data_section_value})
    
    for section_value in get_all_sections_container:

        first_a_tag = section_value.find("a", class_="reference")

        if first_a_tag:
            first_a_tag.decompose()

        reference_check = section_value.find("span", class_="reference") 
        section_text = section_value.get_text().strip().replace('\n', ' ').encode('ascii', 'ignore').decode('ascii')

       

        if ("History:" in section_text): 
            node_addendum = section_text
            node_addendum_pretty = node_addendum.split()
            node_addendum = " ".join(node_addendum_pretty[2:])

        elif ("Cross-reference" in section_text and reference_check is not None):
            node_tags["Cross-reference"] = section_text

        elif ("Annotation" in section_text):
            node_tags["Annotation"] = section_text

        elif ("NOTE:" in section_text):
            node_tags["Note"] = section_text

        else:
            node_text.append(section_text)

    node_name_pattern = r"(\d+\.\d+)\s+(.*?\.)"
    match = re.search(node_name_pattern, node_text[0])


    if match:
        node_name = f"{match.group(1)} {match.group(2)}"

    node_name = f"Section {node_name}"
    node_tags = json.dumps(node_tags)
    node_citation = f"Wis. Stat. § {section_number}"

    node_data = (node_id, top_level_title, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, None, None, node_tags)
    insert_node_ignore_duplicate(node_data)
    

# Needs to be updated for each jurisdiction
def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "wi/",
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
        "wi/statutes/",
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
        "wi/",
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