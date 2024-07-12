import psycopg
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from utils.pydanticModels import Node, NodeID, NodeText, Paragraph, Definition, DefinitionHub, IncorporatedTerms, Reference, ReferenceHub, AddendumType, Addendum, analyze_partial_link
import re
from bs4.element import Tag
import logging
from functools import wraps
from typing import Any, List, Union
import json

# Replacle with the state/country code
JURISDICTION = "us"
SUBJURISDICTION = "federal"
CORPUS = "ecfr"
# No need to change this
TABLE_NAME =  f"{JURISDICTION}_{SUBJURISDICTION}_{CORPUS}"

# Secret API: https://www.ecfr.gov/api/renderer/v1/content/enhanced/2024-03-01/title-50?chapter=VI&part=679&subpart=E&section=679.51


 = "will2"

TOC_URL = "https://www.ecfr.gov/current"
BASE_URL = "https://www.ecfr.gov"
# If you want to skip the first n titles, set this to n
SKIP_TITLE = 0 
# List of words that indicate a node is reserved
RESERVED_KEYWORDS = ["[RESERVED]", "[Reserved]"]
LOGGER = None
LAST_DEFINITION = None


def main():
    
    create_logger()

    
    fix_references()
    #fix_definition_hub_incorporated_definitions()
    # redo_definitions()
    
    
    # corpus_node = insert_jurisdiction_and_corpus_node()
    # scrape_leftover_titles(corpus_node)
    
    
    # for i in range(1, 51):
    #     if i == 7 or i == 35 or i == 40 or i == 48:
    #         continue
        
    #     scrape_per_title(corpus_node, str(i))
    #     break
    # scrape_leftover_titles(corpus_node)
        

# ============================ LOGGER =========================================
def create_logger(logger_level=logging.DEBUG):
    global LOGGER
    # Ensure the logs directory exists
    os.makedirs(os.path.join(DIR, 'logs'), exist_ok=True)

    # Create or get the LOGGER
    LOGGER = logging.getLogger(TABLE_NAME)

    # Optionally clear existing handlers to prevent duplicate messages
    LOGGER.handlers = []

    # Set the logging level
    LOGGER.setLevel(logger_level)

    # Create handlers (file and console)
    file_handler = logging.FileHandler(f"{DIR}/logs/{TABLE_NAME}.log", mode="w")
    console_handler = logging.StreamHandler()

    # Create a logging format
    formatter = logging.Formatter('== %(levelname)s - %(name)s: ==\n    %(message)s\n Trace - (%(filename)s:%(lineno)d)')
    file_handler.setFormatter(formatter)
    
    #console_handler.setFormatter(formatter)
    
    # Add file handler to the LOGGER
    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)
    

    # Add console handler to the LOGGER
    LOGGER.info("Logger Created")

def log_func():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            LOGGER.debug(f"\n ==== Entering {func.__name__} ====")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================ SCRAPING =========================================

@log_func()
def scrape_per_title(node_parent, top_level_title):
    
    with open(f"{DIR}/data/title-{top_level_title}.html", 'r') as read_file:
        html = read_file.read()
    read_file.close()
    
    title_container = BeautifulSoup(html, features="lxml")
    title_container = title_container.find(class_="title")
    LOGGER.debug(f"Finished parsing title-{top_level_title}.html into BS4!")
    name = get_text_clean(title_container.find("h1"))
    #LOGGER.info(name)
    name_start = name.split("-")[0].strip()
    
    
    
    #LOGGER.info(name_start)
    number = name_start.split(" ")[-1]
    #LOGGER.info(number)
    level_classifier = "title"

    id = node_parent.id.add_level(level_classifier, number)
    citation = f"Title {number} of the CFR"
    link = f"{BASE_URL}/current/title-{number}"
    node_type = "structure"

    node_instance = Node(
        id=id,
        citation=citation,
        link=link,
        node_type=node_type,
        level_classifier=level_classifier,
        node_name=name,
        parent=node_parent.node_id,
        top_level_title=number,
    )
    
    insert_node_skip_duplicate(node_instance)
    level_divs = title_container.find_all(recursive=False)
    scrape_level(level_divs, node_instance)


POSSIBLE = ["title", "subtitle", "chapter", "subchapter", "part", "subpart", "subject-group","section", "appendix"]
HEADERS = ["h1", "h2", "h3", "h4", "h5", "h6"]

@log_func()
def scrape_level(level_divs: List[Any], node_parent: Node):

    for i, div in enumerate(level_divs):
        if 'class' not in div.attrs:
            continue
        level_classifier = div['class'][0].lower()
        if level_classifier not in POSSIBLE:
            continue

        if level_classifier == "section" or level_classifier == "appendix":
            try:
                scrape_section(div, node_parent)
            except Exception as e:
                LOGGER.error(f"Error in scrape_section")
            continue
        
        level_component = div['id'].replace("-"," ", 1)
        if level_classifier == "subject-group":
            level_component = level_component.replace("-"," ", 1)
        name = get_text_clean(div.find(HEADERS))
        # NO DASHES ALLOWED IN THE NODE NUMBER OR LEVEL CLASSIFIER.
        # I HAVE SPENT TOO MUCH TIME DEBUGGING THIS DUMB ERROR
        number = level_component.split(" ")[-1].replace("/", "-")
        
        if number == "0":
            number = name.split(" ")[1]

        previous_link = node_parent.link
        top_level_title = node_parent.top_level_title
        
        
        
        citation = create_citation_from_level_classifier(level_classifier, number, name, node_parent)
        
        
        
        id = node_parent.id.add_level(level_classifier, number)


        link = f"{previous_link}/{level_classifier}-{number}"
        if level_classifier == "subject-group":
            link = f"{previous_link}/{div['id']}"
        
        

        status=None
        for word in RESERVED_KEYWORDS:
            if word in name:
                status="reserved"
                break
        
        node_type = "structure"
        node_instance = Node(
            id=id,
            citation=citation,
            link=link,
            node_type=node_type,
            level_classifier=level_classifier,
            top_level_title=top_level_title,
            number=number,
            node_name=name,
            parent=node_parent.id.raw_id,
            status=status
        )
        

        # Try to get source, citation, authority
        # PROBLEM: ERROR in ecfr: https://www.ecfr.gov/current/title-18/chapter-I/subchapter-Q/part-352
        # Sections are all listed underneath part with no tagging. Breaks the scraper
        # FIX THIS LATER
        
        addendum = extract_addendum(div, node_parent)
        node_instance.addendum = addendum
        
        insert_node_skip_duplicate(node_instance)


        level_divs = div.find_all(recursive=False)
        scrape_level(level_divs, node_instance)
    

        


# Also used for appendices    
@log_func()      
def scrape_section(section_div, node_parent: Node):
    global LAST_DEFINITION

    level_classifier = section_div['class'][0]
    html_id = section_div['id']
    
    name_tag = section_div.find("h4")
    path, citation = extract_data_hierarchy_metadata(name_tag)
    last_path = path.split("/")[-1].replace(' ', '%20')
    number = html_id
    number = number.replace("/","-")
    link = f"{node_parent.link}/{last_path}"
    
    new_id = node_parent.id.add_level(level_classifier, number)

    
    name = get_text_clean(name_tag)
    name_tag.decompose()
    node = Node(id=new_id, citation=citation, link=link, node_type="content", level_classifier=level_classifier, number=number, parent=node_parent.id.raw_id, node_name=name, top_level_title=node_parent.top_level_title)
    node.node_text = NodeText()
    node.definitions = DefinitionHub(local_definitions={})
    node.core_metadata = {}
    


    # Deal with citations before recursive scraping
    addendum = extract_addendum(section_div, node_parent)
    node.addendum = addendum

    # Decide definition case, 4 is default
    # Cases 1,2,3, 4 can be determined before recursive scraping. 5 cannot.
    definition_case = 4
    if "definitions" in node_parent.node_name.lower():
        definition_case = 1
        #LOGGER.debug(f"Definition Case 1: {node.node_name}")
    elif "definitions." in node.node_name.lower():
        definition_case = 2
        #LOGGER.debug(f"Definition Case 2: {node.node_name}")
    elif "definitions" in node.node_name.lower():
        definition_case = 3
        #LOGGER.debug(f"Definition Case 2.5: {node.node_name}")
    else:
        pass
        #LOGGER.debug(f"Definition Case 3: {node.node_name}")
    
    paragraph_parent = html_id
    node.node_text.root_paragraph_id = paragraph_parent
    section_divs = section_div.find_all(recursive=False)
    
    recursive_paragraph_scrape(section_divs, paragraph_parent, paragraph_parent, node, definition_case)
    if "table of contents" in node.node_name.lower():
        node.definitions.scope = None
        node.definitions.local_definitions = None
        node = None
        return

    node.node_text.extrapolate_children_from_parents()
    LOGGER.debug(f"Node: {node.node_id}")
    #LOGGER.debug(f"Node Text: {node.node_text}")
    #node.node_text.build_children_map()
    LAST_DEFINITION = None
    
    if node.definitions.local_definitions == {} and node.definitions.scope is None:
            node.definitions = None
        
    elif 'definition_case' in node.core_metadata:
        definition_case = node.core_metadata['definition_case']
    else:
        # Delete the temporary key "UNKOWN" if it exists
        
        
        scope = ""
        # Find the scope of the definition_hub
        if definition_case == 1:
            
            if "sub" in node_parent.level_classifier:
                scope_id = node_parent.parent
            else:
                scope_id = node_parent.node_id
            node.definitions.scope_ids = [scope_id]
            scope = "DEFAULT"
            node.definitions.scope = scope
        # Scope still needs to be found
        if (definition_case == 2 or definition_case == 3 or definition_case == 4 )and node.definitions.scope is None:
            # Find the paragraph in NodeText that has the classification "definition" and has the lowest index
            lowest_index = 999999
            lowest_index_id = None
            parent_index = None
            for k,v in node.node_text.paragraphs.items():
                if v.classification == "definition":
                    
                    if v.index < lowest_index:
                        lowest_index = v.index
                        lowest_index_id = k
                        parent_index = v.parent
            
            disallowed_classifications = ["table-wrapper", "example", "note", "extract", "editorial-note", "effective-date-note", "cross-reference", "image","section-authority"]
            if lowest_index_id is not None:
                try:
                    
                    
                    if node.node_text.paragraphs[parent_index].classification in disallowed_classifications:
                        scope = "PARENT"
                        node.definitions.scope_ids = [node_parent.node_id]
                    else:
                        scope = node.node_text.paragraphs[parent_index].text
                except KeyError:
                    scope = "PARENT"
                    node.definitions.scope_ids = [node_parent.node_id]
                #LOGGER.debug(f"Scope: {scope}")
                node.definitions.scope = scope

        node.core_metadata['definition_case'] = definition_case
    



    if node.node_text.paragraphs == {}:
        node.node_text = None
    else:
        tokens = calculate_node_tokens(node.node_text.to_list_text())
        node.core_metadata["tokens"] = tokens


    if node.core_metadata == {}:
        node.core_metadata = None


    insert_node_allow_duplicate(node)
    
        
    
def scrape_section_other(section_div, node:Node):
    global LAST_DEFINITION

    
    node.node_text = NodeText()
    node.definitions = DefinitionHub(local_definitions={})
    node.core_metadata = {}
    html_id = section_div['id']
    name_tag = section_div.find("h4")
    name_tag.decompose()

    authority = section_div.find(class_="authority")
    source = section_div.find(class_="source")
    citation = section_div.find(class_="citation")
    section_authority = section_div.find(class_="section-authority")
    if authority is not None:
        authority.decompose()
    if source is not None:
        source.decompose()
    if citation is not None:
        citation.decompose()
    if section_authority is not None:
        section_authority.decompose()

                                 
    


    # Deal with citations before recursive scraping
    

    # Decide definition case, 4 is default
    # Cases 1,2,3, 4 can be determined before recursive scraping. 5 cannot.
    definition_case = 4
    
    if "definitions." in node.node_name.lower():
        definition_case = 2
        #LOGGER.debug(f"Definition Case 2: {node.node_name}")
    elif "definitions" in node.node_name.lower():
        definition_case = 3
        #LOGGER.debug(f"Definition Case 2.5: {node.node_name}")
    else:
        pass
        #LOGGER.debug(f"Definition Case 3: {node.node_name}")
    
    paragraph_parent = html_id
    node.node_text.root_paragraph_id = paragraph_parent
    #print(section_div.prettify())
    section_divs = section_div.find_all(recursive=False)
    LOGGER.debug(f"Rescraping for id: {node.node_id}")
    LOGGER.debug(f"Original definition case: {definition_case}")
    recursive_paragraph_scrape(section_divs, paragraph_parent, paragraph_parent, node, definition_case)
    

    node.node_text.extrapolate_children_from_parents()
    #LOGGER.debug(f"Node: {node.node_id}")
    #LOGGER.debug(f"Node Text: {node.node_text}")
    #node.node_text.build_children_map()
    
    # LOGGER.debug(node.definitions.scope)
    # LOGGER.debug(node.definitions.scope_ids)
    # for k,v in node.definitions.local_definitions.items():
    #     LOGGER.debug(f"Key (term): {k}")
    #     LOGGER.debug(f"Value (definition): {v.definition}")
    #     LOGGER.debug(f" Value (source_link): {v.source_link}")
    #     LOGGER.debug(f"Value (source_paragraph): {v.source_paragraph}")
    #     LOGGER.debug(f"Value (subdefinitions): {v.subdefinitions}")
    #     LOGGER.debug(f"Value (is_subterm): {v.is_subterm}")
        
    
    LAST_DEFINITION = None
    
    if node.core_metadata and 'definition_case' in node.core_metadata:
        definition_case = node.core_metadata['definition_case']
        LOGGER.debug(f"Overwriting definition case: {definition_case}")
    
    if node.definitions.local_definitions == {} and node.definitions.scope is None:
            if definition_case == 2 or definition_case == 3:
                try:
                    node.definitions.scope = node.node_text.to_list_text()[0]
                except:
                    node.core_metadata['broken_section'] = True

            else:
                LOGGER.debug(f"Setting definitions to None")
                node.definitions = None
        
    else:
        # Delete the temporary key "UNKOWN" if it exists
        
        
        scope = ""
        node_parent = node.id.pop_level()
    
        # Find the scope of the definition_hub
        if definition_case == 1:

            
            if "sub" in node_parent.current_level:
                scope_id = node_parent.pop_level().raw_id
            else:
                scope_id = node_parent.raw_id
            node.definitions.scope_ids = [scope_id]
            scope = "DEFAULT"
            node.definitions.scope = scope
        # Scope still needs to be found
        if (definition_case == 2 or definition_case == 3 or definition_case == 4 or definition_case == 6 )and node.definitions.scope is None:
            # Find the paragraph in NodeText that has the classification "definition" and has the lowest index
            LOGGER.debug(f"Scope is None and definition case is {definition_case}")
            lowest_index = 999999
            lowest_index_id = None
            parent_index = None
            for k,v in node.node_text.paragraphs.items():
                if v.classification == "definition":
                    
                    if v.index < lowest_index:
                        lowest_index = v.index
                        lowest_index_id = k
                        parent_index = v.parent
            
            disallowed_classifications = ["table-wrapper", "example", "note", "extract", "editorial-note", "effective-date-note", "cross-reference", "image","section-authority"]
            if lowest_index_id is not None:
                try:
                    
                    
                    if node.node_text.paragraphs[parent_index].classification in disallowed_classifications:
                        scope = "PARENT"
                        node.definitions.scope_ids = [node_parent.raw_id]
                    else:
                        scope = node.node_text.paragraphs[parent_index].text
                except KeyError:
                    scope = "PARENT"
                    node.definitions.scope_ids = [node_parent.raw_id]
                LOGGER.debug(f"Scope: {scope}")
                node.definitions.scope = scope

        node.core_metadata['definition_case'] = definition_case
    


    LOGGER.debug(f"Node: {node.definitions}")
    if node.node_text.paragraphs == {}:
        node.node_text = None
    else:
        tokens = calculate_node_tokens(node.node_text.to_list_text())
        node.core_metadata["tokens"] = tokens


    if node.core_metadata == {}:
        node.core_metadata = None

    util.pydantic_update(table_name="definition_diff",nodes=[node], where_field="id", include=None, user=)
    #insert_node_allow_duplicate(node)
    
    
        

           
# us/federal/ecfr/title=1/chapter=IV/part=500/section=500.103 - Test For Combining Paragraphs
def recursive_paragraph_scrape(section_divs, paragraph_id: str, paragraph_parent: str, node: Node, definition_case: str):
    global LAST_DEFINITION
    
    
    next_definition_case = definition_case
    #LOGGER.debug(f"Paragraph Parent: {paragraph_parent}, Paragraph ID: {paragraph_id}")
    for i, tag in enumerate(section_divs):
        #LOGGER.debug(f"Tag: {tag.name}, {tag.attrs}")
        #LOGGER.debug(f"Paragraph Parent: {paragraph_parent}, Paragraph ID: {paragraph_id}")
        
        if tag.name == "div":
            if 'class' in tag.attrs:
                #LOGGER.debug(f"Div Class: {tag['class']}")
                # Don't recurse into seal-blocks
                if 'seal-block' in tag['class'] or  'seal-block-header' in tag['class']:
                    continue

                # Don't recurse into tables, examples, or notes; add them as a paragraph
                disallowed_classifications = ["table-wrapper", "example", "note", "extract", "editorial-note", "effective-date-note", "cross-reference", "image", "footnotes", "fr-cross-reference"]
                is_disallowed = False
                for classification in disallowed_classifications:
                    if classification in tag['class']:
                        is_disallowed = True
                        break
                #print(is_disallowed)
                if is_disallowed:
                    index = node.node_text.length
                    
                    text = get_text_clean(tag)
                    classification = tag['class'][0]
                    paragraph = Paragraph(index=index, text=text, parent=paragraph_parent, children=[], classification=classification)
                    
                    # Add the paragraph. It it's unique, add it to the children_ids
                    added_paragraph_id = (node.node_text.add_paragraph(paragraph, paragraph_id))
                    
                    continue
            try:
                new_paragraph_id = tag['id']
            except:
                new_paragraph_id = paragraph_id
            #LOGGER.debug(f"New Paragraph ID: {new_paragraph_id}")
            recursive_paragraph_scrape(tag.find_all(recursive=False), new_paragraph_id, paragraph_id, node, next_definition_case)
            

            continue
                   
        # Handle single images
        elif tag.name == "a" and tag.find("img") is not None:
            link = tag['href']

            text = f"IMAGE [*{link}*]"
            index = node.node_text.length
            
            
            paragraph = Paragraph(index=index, text=text, parent=paragraph_parent, children=[], classification="image")
            
            added_paragraph_id = node.node_text.add_paragraph(paragraph, paragraph_id)
            
            
            continue
        elif tag.name == "p" or tag.name == "span":
                #LOGGER.debug(f"P case!")
                if 'id' in tag.attrs:
                    paragraph_id = tag['id']

                index = node.node_text.length
                text, references = extract_paragraph_text_and_references(tag)
                

                if references is not None:
                    paragraph = Paragraph(index=index, text=text, parent=paragraph_parent, children=[], references=references)
                else:
                    paragraph = Paragraph(index=index, text=text, parent=paragraph_parent, children=[])
                LOGGER.debug(f"P: {paragraph.text}")
                #LOGGER.debug(f"Definition Case: {definition_case}")

                classification = None
                # This paragraph is explicitly tagged as a term
                if 'data-term' in tag.attrs:
                    LOGGER.debug(f"Case: Data-Term")
                    classification = "definition"

                    try:
                        term = get_text_clean(tag.find("em"))
                        
                    except:
                        term = text.split("“")[1].split("”")[0]
                    if "Example " in term:
                        paragraph.topic = term
                        paragraph.classification = classification
            
                        added_paragraph_id = node.node_text.add_paragraph(paragraph, paragraph_id)
                        continue
                    if term.endswith("."):
                        term = term[:-1]
                    term = term.lower()
                    LOGGER.debug(f"Term: {term}")

                    
                    

                    source_section = node.node_id
                    source_paragraph = paragraph_id
                    source_link = f"{node.link}#{paragraph_id}"

                    definition = Definition(definition=text, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link)
                    # us/federal/ecfr/title=5/chapter=LX/part=7001/section=7001.102

                    mark_as_term = False
                    if term not in node.definitions.local_definitions:
                        mark_as_term = True
                        node.definitions.local_definitions[term] = definition
                    
                    # This paragraph is ALSO a subdefinition
                    if definition_case == 6:
                        if mark_as_term:
                            subdefinition = Definition(definition=term, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link, is_subterm=True)
                            node.core_metadata['nested_terms'] = True
                        else:
                            subdefinition = definition
                        if not add_subdefinition_to_parent(node.definitions.local_definitions.values(), paragraph_parent, subdefinition, node):
                        # This is an ugly disgusting hack, and I'm sorry I wrote it
                            if LAST_DEFINITION.subdefinitions is None:
                                LAST_DEFINITION.subdefinitions = []    
                            LAST_DEFINITION.subdefinitions.append(subdefinition)
                            

                        LAST_DEFINITION = subdefinition
                    else:
                        LAST_DEFINITION = definition
                    
                # This paragraph is explicitly tagged a subdefinition
                elif "data-disable" in tag.attrs:
                    LOGGER.debug(f"Case: Data-Disable")
                    classification = "subdefinition"
                    
                    subdefinition = Definition(definition=text, source_section=node.node_id, source_paragraph=paragraph_id, source_link=f"{node.link}#{paragraph_id}")
                    # Search the definition hub for the term defined in the parent of this subdefinition
                    
                    # Calls the helper to find the parent definition (or subdefinition) and add the subdefinition to it
                    if not add_subdefinition_to_parent(node.definitions.local_definitions.values(), paragraph_parent, subdefinition, node):
                        #LOGGER.error(f"Subdefinition {subdefinition} could not be added to parent {paragraph_parent}")
                        # This is an ugly disgusting hack, and I'm sorry I wrote it
                        if LAST_DEFINITION.subdefinitions is None:
                            LAST_DEFINITION.subdefinitions = []
                        LAST_DEFINITION.subdefinitions.append(subdefinition)
                    LAST_DEFINITION = subdefinition

                # This paragraph contains an emphasis. Could be a definition 5, subdefinition, or a topic
                elif tag.find("em", recursive=False) is not None:
                    
                    LOGGER.debug(f"Case: Emphasis")
                    topic = get_text_clean(tag.find("em", recursive=False))
                    
                    if definition_case == 2 or definition_case == 3:
                        if topic.endswith("."):
                            topic = topic[:-1]
                        topic = topic.lower()
                        classification = "definition"
                        term = topic
                        #definition_text = text.replace(term, "", 1)
                        source_section = node.node_id
                        source_paragraph = paragraph_id
                        source_link = f"{node.link}#{paragraph_id}"
                        
                        definition = Definition(definition=text, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link)
                        mark_as_term = False
                        if term not in node.definitions.local_definitions:
                            mark_as_term = True
                            node.definitions.local_definitions[term] = definition
                        definition_case = 5
                        LAST_DEFINITION = definition


                    # A parent paragraph is a definition. Topic is the term
                    elif definition_case >= 5:
                        if "Example " in topic:
                            paragraph.topic = topic
                            paragraph.classification = classification
                
                            added_paragraph_id = node.node_text.add_paragraph(paragraph, paragraph_id)
                            continue
                        if topic.endswith("."):
                            topic = topic[:-1]
                        topic = topic.lower()
                        
                        classification = "definition"
                        term = topic
                        #definition_text = text.replace(term, "", 1)
                        source_section = node.node_id
                        source_paragraph = paragraph_id
                        source_link = f"{node.link}#{paragraph_id}"
                        
                        definition = Definition(definition=text, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link)
                        mark_as_term = False
                        if term not in node.definitions.local_definitions:
                            mark_as_term = True
                            node.definitions.local_definitions[term] = definition
                        
                        # This paragraph is ALSO a subdefinition
                        if definition_case == 6:
                            if mark_as_term:
                                subdefinition = Definition(definition=term, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link, is_subterm=True)
                                node.core_metadata['nested_terms'] = True
                            else:
                                subdefinition = definition
                            if not add_subdefinition_to_parent(node.definitions.local_definitions.values(), paragraph_parent, subdefinition, node):
                            # This is an ugly disgusting hack, and I'm sorry I wrote it
                                if LAST_DEFINITION.subdefinitions is None:
                                    LAST_DEFINITION.subdefinitions = []    
                                LAST_DEFINITION.subdefinitions.append(subdefinition)
                                

                            LAST_DEFINITION = subdefinition
                        else:
                            LAST_DEFINITION = definition
                    
                    # Definition case 5 is first found
                    elif "definitions." in topic.lower() and definition_case != 5 and definition_case != 6:
                        #LOGGER.debug(f"Case: Definitions.")
                        definition_case = 5
                        classification = "scope"
                        if topic.endswith("."):
                            topic = topic[:-1]
                        topic = topic.lower()
                    
                        # The only word in this paragraph is an emphasized "Definitions." Scope should be PARENT
                        if text.replace(topic, "", 1).strip() == "":
                            node.definitions.scope = "PARENT"
                            node.definitions.scope_ids = [paragraph_parent]
                        # Scope is sibling to "Definitions."
                        else:
                            node.definitions.scope = text
                        node.core_metadata['definition_case'] = definition_case
                    # Not a definition, it's simply an emphasized piece of text, mark as topic
                    else:
                        paragraph.topic = topic
                # Handle weird cases where definitions are denoted by quotes not <em>
                elif '“' in text and '”' in text and definition_case != 6:
                    #LOGGER.debug(f"Case: Quotes")
                    
                    if definition_case == 5 or definition_case == 2:
                        
                        classification = "definition"
                        term = text.split("“")[1].split("”")[0]
                        if term.endswith("."):
                            term = term[:-1]
                        term = term.lower()
                        #definition_text = text.replace(f"“{term}”", "", 1)
                        source_section = node.node_id
                        source_paragraph = paragraph_id
                        source_link = f"{node.link}#{paragraph_id}"
                        definition = Definition(definition=text, source_section=source_section, source_paragraph=source_paragraph, source_link=source_link)
                        if term not in node.definitions.local_definitions:
                            node.definitions.local_definitions[term] = definition
                        LAST_DEFINITION = definition
                        definition_case = 5
                # This is still a subdefinition
                elif definition_case == 6:
                    classification = "subdefinition"
                    #LOGGER.debug(f"Case: Subdefinition")
                    
                    subdefinition = Definition(definition=text, source_section=node.node_id, source_paragraph=paragraph_id, source_link=f"{node.link}#{paragraph_id}")
                    # Search the definition hub for the term defined in the parent of this subdefinition
                    
                    # Calls the helper to find the parent definition (or subdefinition) and add the subdefinition to it
                    if not add_subdefinition_to_parent(node.definitions.local_definitions.values(), paragraph_parent, subdefinition, node):
                        #LOGGER.error(f"Subdefinition {subdefinition} could not be added to parent {paragraph_parent}")
                        # This is an ugly disgusting hack, and I'm sorry I wrote it
                        if LAST_DEFINITION.subdefinitions is None:
                            LAST_DEFINITION.subdefinitions = []
                        LAST_DEFINITION.subdefinitions.append(subdefinition)
                    LAST_DEFINITION = subdefinition

                # Check this: us/federal/ecfr/title=12/chapter=III/subchapter=B/part=337/section=337.6
                
                

                paragraph.classification = classification
                
                added_paragraph_id = node.node_text.add_paragraph(paragraph, paragraph_id)
                #
                # Paragraph was a duplicate. Update the definition text
                if added_paragraph_id != paragraph_id:
                    update_definition_text(node.definitions.local_definitions.values(), paragraph_id, text, node)

                # A term has been added, the definition case is now 6
                
                if definition_case == 5 and node.definitions.local_definitions != {}:
                    #LOGGER.debug(f"Setting Definition Case 6:")
                    next_definition_case = 6
                    node.core_metadata['definition_case'] = 6
        else:
            LOGGER.critical(f"Unknown tag: {tag.name}\n{tag}")
            index = node.node_text.length
            
            text = get_text_clean(tag)
            try:
                classification = tag['class'][0]
            except:
                classification = None
            paragraph = Paragraph(index=index, text=text, parent=paragraph_parent, children=[], classification=classification)
            
            if 'unkown_tags' not in node.core_metadata:
                node.core_metadata['unkown_tags'] = []
            node.core_metadata['unkown_tags'].append({"paragraph_id": paragraph_id, "attrs": tag.attrs})
            added_paragraph_id = node.node_text.add_paragraph(paragraph, paragraph_id)
            continue
    
    
    

# Correctly places a subdefinition into the parent definition     
def add_subdefinition_to_parent(defs: List[Definition], parent_id: str, subdefinition: Definition, node: Node) -> bool:
    for definition in defs:
        
        if definition.source_paragraph == parent_id and (definition.is_subterm is None or definition.is_subterm == False):
            if definition.subdefinitions is None:
                definition.subdefinitions = []
            definition.subdefinitions.append(subdefinition)
            return True
        if definition.subdefinitions is not None:
            if add_subdefinition_to_parent(definition.subdefinitions, parent_id, subdefinition, node):
                node.core_metadata['nested_subdefinitions'] = True
                return True
    return False

def update_definition_text(defs: List[Definition], target_id: str, text: str, node: Node) -> bool:    
    for definition in defs:
        if definition.source_paragraph == target_id:
            definition.definition += "\n" + text
            return True
        if definition.subdefinitions is not None:
            if update_definition_text(definition.subdefinitions, target_id, text, node):
                return True
    return False

def extract_addendum(div, node_parent: Node) -> Union[None, Addendum]:
    # Get the parent's authority and source
    #print("HERE!")
    addendum = Addendum()
    if node_parent.addendum is not None:
        parent_authority = node_parent.addendum.authority
        parent_source = node_parent.addendum.source
        parent_history = node_parent.addendum.history
    else:
        parent_authority = None
        parent_source = None
        parent_history = None

    authority_div = div.find_all("div", class_="authority", recursive=False)
    authority_references = ReferenceHub()
    if authority_div == []:
        authority_div = None
        

    section_authority_div = div.find_all("div", class_="section-authority", recursive=False)
    if section_authority_div == []:
        section_authority_div = None

    if section_authority_div is None and authority_div is None:
        history_references = None

    authority_text = ""
    authority_prefix = None

    if authority_div is not None:
        for i, div in enumerate(authority_div):
            LOGGER.debug(f"Div @ index {i}: {div.attrs}")
            authority_text_temp, authority_references = extract_paragraph_text_and_references(div, ref_dict=authority_references)
            #LOGGER.debug(f"Authority Text: {authority_text_temp}")
            authority_text += authority_text_temp
            
        for div in authority_div:
            div.decompose()
    if section_authority_div is not None:
        for div in section_authority_div:
            section_authority_text_temp, authority_references = extract_paragraph_text_and_references(div, ref_dict=authority_references)
            authority_text += section_authority_text_temp
        for div in section_authority_div:
            div.decompose()
    elif parent_authority is not None:
        if parent_authority.prefix is not None:
            authority_prefix = parent_authority.prefix
        else:
            authority_prefix = f"Per {node_parent.citation}:"
        authority_text = parent_authority.text
        authority_references = parent_authority.references

    if parent_authority is None and authority_div is None and section_authority_div is None:
        authority_addendum = None
    else:
        authority_addendum = AddendumType(type="authority", text=authority_text, prefix=authority_prefix, references=authority_references)

    
    # Add the authority to the node_instance, and add it to the addendum
    addendum.authority = authority_addendum
    
    
    # Get source
    source_div = div.find_all("div", class_="source", recursive=False)
    source_references = ReferenceHub()
    if source_div == []:
        source_div = None
        source_references = None

    source_text = ""
    source_prefix = None

    if source_div is not None:
        for div in source_div:
            source_text_temp, source_references = extract_paragraph_text_and_references(div, ref_dict=source_references)
            source_text += source_text_temp
        for div in source_div:
            div.decompose()
    elif parent_source is not None:
        if parent_source.prefix is not None:
            source_prefix = parent_source.prefix
        else:
            source_prefix = f"Per {node_parent.citation}:"
        source_text = parent_source.text
        source_references = parent_source.references

    if parent_source is None and source_div is None:
        source_addendum = None
    else:
        source_addendum = AddendumType(type="source", text=source_text, prefix=source_prefix, references=source_references)
    # Add the source to the node_instance, and add it to the addendum
    addendum.source = source_addendum


    history_div = div.find_all("p", class_="citation", recursive=False)
    history_text = ""
    history_prefix = None
    history_references = ReferenceHub()
    if history_div == []:
        history_div = None
        history_references = None

    if history_div is not None:
        
        for div in history_div:
            history_text_temp, history_references = extract_paragraph_text_and_references(div, ref_dict=history_references)
            history_text += history_text_temp
        for div in history_div:
            div.decompose()
    elif parent_history is not None:
        if parent_history.prefix is not None:
            history_prefix = parent_history.prefix
        else:
            history_prefix = f"Per {node_parent.citation}:"
        history_text = parent_history.text
        history_references = parent_history.references

    if parent_history is None and history_div is None:
        history_addendum = None
    else:
        history_addendum = AddendumType(type="history", text=history_text, prefix=history_prefix, references=history_references)
    # Add the source to the node_instance, and add it to the addendum
    addendum.history = history_addendum
    if addendum.authority is None and addendum.source is None and addendum.history is None:
        addendum = None
    return addendum

def increment_copy_number(paragraph_id: str) -> str:
    if "-copy-" in paragraph_id:
        base_id, copy_number = paragraph_id.rsplit("-copy-", 1)
        new_copy_number = int(copy_number) + 1
        new_id = f"{base_id}-copy-{new_copy_number}"
    else:
        new_id = f"{paragraph_id}-copy-1"
    return new_id

def calculate_node_tokens(node_text: list[str]) -> int:
    tokens = 0
    for paragraph in node_text:
        tokens += util.num_tokens_from_string(paragraph)
    return tokens

# I AM A FUCKING GENIUS for this function + recursive_scrape
@log_func()
def scrape_leftover_titles(node_parent):
    # ["7", "40", "48"]
    for i in [ "7", "40", "48"]:
        top_level_title = i
        with open(f"{DIR}/data/title-{top_level_title}.json", 'r') as read_file:
            json_structure = read_file.read()
        read_file.close()

        json_dict = json.loads(json_structure)
        node_parent.link = TOC_URL
        node_parent.top_level_title = top_level_title
        recursive_scrape(json_dict, node_parent)
    
# Recursively scrape the JSON data until we hit a "PART". Access the API url for the HTML, and then slip right
# Into the regular scraping pipeline as if nothing ever happened. Pat on the back, Will
@log_func()
def recursive_scrape(current_dict, node_parent):

    number = current_dict['identifier'].replace(" ", "-")
    level_classifier = current_dict['type'].lower()
    status=None
    if current_dict['reserved']:
        status = "reserved"
    node_type = "structure"
    name = current_dict['label']
    #LOGGER.info(f"Name: {name}, Number: {number}, Level: {level_classifier}")
    if level_classifier == "appendix":
        raw_number = number.split("-")[1]
        if raw_number == "to":
            raw_number = ""
        citation = create_citation_from_level_classifier(level_classifier, raw_number, name, node_parent)
    else:
        citation = create_citation_from_level_classifier(level_classifier, number, name, node_parent)
    #LOGGER.info(f"Citation: {citation}")

    if level_classifier == "subject-group":
        link = f"{node_parent.link}/{name}"
    elif level_classifier == "appendix":
        number = number.replace(" ", "-")
        number=number.replace("-","%20")
        link = f"{node_parent.link}/{level_classifier}-{number}"
    else:
        link = f"{node_parent.link}/{level_classifier}-{number}"
    id = node_parent.id.add_level(level_classifier, number)
    if level_classifier == "appendix":
        number = raw_number
    node_instance = Node(
        id=id,
        citation=citation,
        link=link,
        node_type=node_type,
        level_classifier=level_classifier,
        top_level_title=node_parent.top_level_title,
        number=number,
        node_name=name,
        parent=node_parent.id.raw_id,
        status=status,
        core_metadata={"wrong_parent": True}

    )
    
    
    if level_classifier == "part":
        insert_node(node_instance)
       
        # Read in the html from this link
        # /title-40?chapter=VIII&part=1800&subpart=C&section=1800.101
        # /title-40?chapter=VIII&part=1800&subpart=C&section=1800.101
        base_link = f"https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/"
        
        for i, level in enumerate(node_instance.id.component_classifiers):
            if i <=2:
                continue
            classifier = level.lower()
            #LOGGER.debug(f"Classifier: {classifier}")
            number = node_instance.id.component_numbers[i].replace(" ","-")
            #LOGGER.debug(f"Number: {number}")
            
            if classifier == "title":
                base_link += f"title-{number}?"
            else:
                base_link += f"{classifier}={number}&"
        base_link = base_link[:-1]
        LOGGER.debug(f"Constructed Link: {base_link}")

        response = urllib.request.urlopen(base_link)
        data = response.read()      # a `bytes` object
        text = data.decode('utf-8') # a `str`;
        soup = BeautifulSoup(text, features="html.parser").find("div")
        level_divs = soup.find_all(recursive=False)
        scrape_level(level_divs, node_instance)
        pass
    else:
        insert_node_allow_duplicate(node_instance)
        if "children" in current_dict:
            for new_dict in current_dict['children']:
                recursive_scrape(new_dict, node_instance)


# ============================ SCRAPING HELPERS =========================================
# Handle images how? TODO
def extract_paragraph_text_and_references(html_element, ref_dict=None) -> tuple[str, Union[None, ReferenceHub]]:
    if ref_dict is None:
        ref_dict = ReferenceHub()
    paragraph_text = get_text_clean(html_element, direct_children_only=True)
    new_paragraph_text = []
    all_a_tags = html_element.find_all("a")
    start = 0
    for i, a_tag in enumerate(all_a_tags):
        #LOGGER.debug(f"A Tag @ index{i}: {a_tag.attrs}")
        txt = get_text_clean(a_tag)
        #LOGGER.debug(f"Txt: {txt}")


        target_link = a_tag['href']
        #LOGGER.debug(f"Target Link: {target_link}")
        # LOGGER.debug(f"Txt: {txt}")
        if ".png" in target_link:
            a_tag.string = target_link
            continue
        if "http" not in target_link:
            target_link = f"{BASE_URL}{target_link}"

        
        placeholder = f"[*{target_link}*]"
        start_index = paragraph_text.find(txt, start)
        end_index = start_index + len(txt)

        # Append the text before the link, the link text, and the placeholder to the list
        new_paragraph_text.append(paragraph_text[start:end_index])
        new_paragraph_text.append(' ')
        new_paragraph_text.append(placeholder)

        # Update the start index for the next iteration
        start = end_index
        # paragraph_text = paragraph_text.replace(txt, f"{txt} {placeholder}")
        target_corpus = None
        
        if "uscode" in target_link:
            target_corpus = "us/federal/usc"
        elif "ecfr.gov" in target_link:
            target_corpus = None
        elif "federalregister" in target_link:
            target_corpus = "us/federal/fr"
        elif "link/plaw" in target_link:
            target_corpus = "us/federal/publ"
        else:
            target_corpus = "other"

        
        
        ref = Reference(text=txt, placeholder=placeholder, corpus=target_corpus)
        
        ref_dict.references[target_link] = ref
    new_paragraph_text.append(paragraph_text[start:])

    # Join the list into a single string
    paragraph_text = ''.join(new_paragraph_text)

    if ref_dict.references == {}:
        ref_dict = None
    return paragraph_text, ref_dict

def create_citation_from_level_classifier(level_classifier, number, name, node_parent):
    
    citation = None
    parent_number = node_parent.number
    top_level_title = node_parent.top_level_title
    
    #LOGGER.debug(f"Level Classifier: {level_classifier.capitalize()}, Number: {number}, Top Level Title: {top_level_title}")
    # Get all different citations, based on the level_classifier
    if level_classifier == "title":
        citation = f"Title {number} of the CFR"
    if level_classifier == "subtitle":
        citation = f"{top_level_title} CFR Subtitle {number}"
        

    if level_classifier == "chapter":
        citation = f"{top_level_title} CFR Chapter {number}"
    # 40 CFR Chapter I Subchapter A
    elif level_classifier == "subchapter":
        # Find the chapter_number from the parent link. Get the number after the last "-"
        citation = f"{top_level_title} CFR Chapter {parent_number} Subchapter {number}"
        
    
    # 40 CFR Part 1
    elif level_classifier == "part":
        citation = f"{top_level_title} CFR Part {number}"
    # 40 CFR Part 1 Subpart A
    elif level_classifier == "subpart":
        citation = f"{top_level_title} CFR Part {parent_number} Subpart {number}"

    if level_classifier == "subject-group":
        citation = f"{node_parent.citation}-{name}"
    if level_classifier == "appendix":
        citation = f"Appendix {number} to {node_parent.citation}"
    if level_classifier == "section":
        citation = f"{node_parent.citation}-{name}"

    return citation

def read_experimental():
    for i in range(1, 51):
        LOGGER.debug(f"Attempting title-{i}.html")
        try:
            link = f"https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-{i}"
            response = urllib.request.urlopen(link)
            LOGGER.debug(" - Success")

        except:
            LOGGER.debug(" - Failed")
            continue
        
        data = response.read()      # a `bytes` object

        with open(f"{DIR}/data/title-{i}.html", "wb") as write_file:
            write_file.write(data)
        write_file.close()

def extract_data_hierarchy_metadata(h_tag):
    # Extract the 'data-hierarchy-metadata' attribute from the h4 tag
    metadata_json_str = h_tag['data-hierarchy-metadata']
    
    # Parse the JSON string into a Python dictionary
    metadata = json.loads(metadata_json_str)
    
    # Extract the 'path' and 'citation' from the metadata
    path = metadata['path']
    citation = metadata['citation']
    
    return path, citation



# ============================ NODE INSERTS =========================================
@log_func()
def insert_node_allow_duplicate(node_instance: Node):
    
    base_node_id = node_instance.node_id
    
    for i in range(2, 10):
        try:
            insert_node(node_instance)
            LOGGER.info(f"-Adding: {node_instance.node_id}")
            
            break
        except psycopg.errors.UniqueViolation as e:
            print(f"** Found duplicate: {node_instance.node_id}")
            node_instance.id = NodeID(raw_id=f"{base_node_id}-v{i}")
            node_instance.status = "DUPLICATE"
        continue

@log_func()
def insert_node_skip_duplicate(node_instance: Node):
    """
    Insert a node, but skip it if it already exists. Returns True if skipped, False if inserted.
    """

    try:
        insert_node(node_instance)
        LOGGER.info(f"-Adding: {node_instance.node_id}")
        return False
    except psycopg.errors.UniqueViolation as e:
        
        LOGGER.debug("** Skipping: %s",node_instance.node_id)

        return True

@log_func()
def insert_jurisdiction_and_corpus_node():
    jurisdiction_id = f"{JURISDICTION}"
    
    jurisdiction_id = NodeID(raw_id=jurisdiction_id)
    
    jurisdiction_node = Node(
        id=jurisdiction_id,
        citation=f"Jurisdiction: {JURISDICTION}",
        link=None,
        node_type="jurisdiction",
        level_classifier="JURISDICTION",
        node_name=f"{JURISDICTION}",
    )
    insert_node_skip_duplicate(jurisdiction_node)
    #print(jurisdiction_node.node_id)
    subjurisdiction_id = jurisdiction_node.id.add_starter_level(SUBJURISDICTION)
    #LOGGER.debug("Subjurisdiction ID: %s", subjurisdiction_id)

    subjurisdiction_node = Node(
        id=subjurisdiction_id,
        citation=f"Subjurisdiction: {SUBJURISDICTION}",
        link=None,
        node_type="subjurisdiction",
        level_classifier="SUBJURISDICTION",
        node_name=f"{SUBJURISDICTION}",
        parent=jurisdiction_node.id.raw_id
    )
    insert_node_skip_duplicate(subjurisdiction_node)
    #print(subjurisdiction_node.node_id)

    corpus_id = subjurisdiction_node.id.add_starter_level(CORPUS)
    #LOGGER.debug("Corpus ID: %s", corpus_id)
    corpus_node = Node(
        id=corpus_id,
        citation=f"Corpus: {CORPUS}",
        link=None,
        node_type="corpus",
        level_classifier="CORPUS",
        node_name=f"{CORPUS}",
        parent=subjurisdiction_node.id.raw_id
    )
    insert_node_skip_duplicate(corpus_node)
    return corpus_node


def insert_node(node_instance):
    util.pydantic_insert(TABLE_NAME, [node_instance], include=None, user=)
    return

# ============================ GENERIC SOUP HELPERS =========================================
def get_text_clean(element, direct_children_only=False):
    '''
    Get text from BeautifulSoup element, clean it, and return it.
    element: BeautifulSoup element (Tag, NavigableString, etc.)
    direct_children_only: If True, only get the text from the direct children of the element
    '''
    if element is None:
        raise ValueError("==== Element is None in get_text_clean! ====")
    
    # Only allow the get_text() function if the element is a BS4 Tag
    if not isinstance(element, Tag):
        direct_children_only = True

    # Get all direct children text, the XML way
    if direct_children_only:
        text = element.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    # Get all chidlren text, Soup function
    else:
        text = element.get_text().replace('\xa0', ' ').replace('\r', ' ').replace('\n', '').strip()
    

    # Remove all text inbetween < >, leftover XML/HTML elements
    clean_text = re.sub('<.*?>', '', text)

    # Replace all stupid weird unicode characters with their regular version
    clean_text = clean_text.replace("—", "-").replace("–", "-")
    return clean_text

def debug_soup_to_file(soup, filename=""):
    with open(f"{DIR}/data/debug_soup{filename}.txt", "w") as write_file:
        write_file.write(soup.prettify())
    write_file.close()
    return

def remove_all_br_tags(soup, verbose=False):
    num_unwrapped = 0
    num_decomposed = 0
    for br in soup.find_all('br'):
        length = len(br.find_all(recursive=False))
        
        if length >= 1:
            num_unwrapped += 1
            br.unwrap()
            
        else:
            num_decomposed += 1
            br.decompose()
    if verbose:
        print(f"== Nuking <br> Tags ==\nUnwrapped: {num_unwrapped}\nDecomposed: {num_decomposed}\n=====================")
    soup.smooth()

# ===== FIXING FUNCTIONS =====

def redo_definitions():
    #sql_select = f"SELECT * FROM definition_diff WHERE id = 'us/federal/ecfr/title=12/chapter=II/subchapter=A/part=208/subpart=H/section=208.82';"
    #sql_select = f"SELECT * FROM definition_diff WHERE definitions is not Null AND not definitions ? 'local_definitions';"
    sql_select = f"SELECT * FROM definition_diff WHERE definitions is Null AND node_text is not Null;"
    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    fak_link = f"https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/"
    for row in rows:
        base_link = fak_link
        if row.id.raw_id == "us/federal/ecfr/title=47/chapter=I/subchapter=C/part=73/subpart=E/section=73.641":
            continue
        
        for i, level in enumerate(row.id.component_classifiers):
            if i <=2:
                continue
            classifier = level.lower()
            #LOGGER.debug(f"Classifier: {classifier}")
            number = row.id.component_numbers[i].replace(" ","-")
            #LOGGER.debug(f"Number: {number}")
            
            if classifier == "title":
                base_link += f"title-{number}?"
            else:
                if classifier == "subject-group":
                    classifier = "subject_group"
                if classifier == "appendix":
                    number = number.replace("-", "%20")
                    
                base_link += f"{classifier}={number}&"
        base_link = base_link[:-1]
        LOGGER.debug(f"Node ID: {row.id.raw_id}")
        LOGGER.debug(f"Constructed Link: {base_link}")
        
        try:
        
            response = urllib.request.urlopen(base_link)
            data = response.read()      # a `bytes` object
            text = data.decode('utf-8')
            soup = BeautifulSoup(text, features="html.parser")
            #print(soup.prettify())
        except:
            LOGGER.error(f"Could not find link: {base_link}")
            raise ValueError(f"Could not find link: {base_link}")
            
        
        section_div = soup.find(class_=classifier)
            
        
            
        scrape_section_other(section_div, row)


        
def fix_definition_hub_incorporated_definitions():
    sql_select = f"SELECT * FROM us_federal_ecfr WHERE node_type = 'hub' AND definitions ? 'incorporated_definitions';"

    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    for row in rows:
        print(f"=====\n{row.id.raw_id}")
        definitions: DefinitionHub = row.definitions
        incorporated_definitions = definitions.incorporated_definitions
        print(f"Source IDs: {definitions.scope_ids}")
        print(f"Incorporated Definitions: {incorporated_definitions}")
        for inc in incorporated_definitions:
            # If corpus is not none, it's not from the ECFR
            if inc.import_source_corpus is not None:
                continue
            if inc.import_source_link is None:
                continue
            if inc.import_source_link == "":
                continue
            print()
            #print(inc)
            
            source_link = inc.import_source_link
            if "#" in source_link:
                source_link, paragraph_id = source_link.split("#")
                if not inc.terms:
                    inc.terms = []
                inc.terms.append(paragraph_id)
            corrected_link, corrected_id = analyze_partial_link(source_link, )
            if corrected_link is None:
                continue
            if corrected_id != inc.import_source_id:
                print(f"Old ID: {inc.import_source_id}")
                print(f"New ID: {corrected_id}")
                print(f"New Link: {corrected_link}")
            inc.import_source_id = corrected_id
        row.definitions.incorporated_definitions = incorporated_definitions
        util.pydantic_update("us_federal_ecfr", [row], where_field="id", include=None, user=)
        
            

            
def find_all_hub_sources():
    # Select all of my definition hubs
    sql_select = f"SELECT * FROM us_federal_ecfr WHERE node_type = 'hub';"
    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    sources = set()
    source_dict = {}
    for row in rows:
        definitions: DefinitionHub = row.definitions
        # For every hub, find the list of source_ids
        source_ids = definitions.scope_ids
        hub_id = row.id.raw_id
        if hub_id not in source_dict:
            source_dict[hub_id] = []
        for id in source_ids:
            
            
            source_dict[hub_id].append(id)
            sources.add(id)
    
    # Sources should now be a list of IDs of my database that have gone into the definition hub
    with open(f"hub_sources.txt", "w") as write_file:
        for source in sources:
            write_file.write(f"{source}\n")
    write_file.close()
    with open(f"hub_sources_dict.json", "w") as write_file:
        write_file.write(json.dumps(source_dict))
    write_file.close()


def find_bad_definition_rows():
    with open('hub_sources.txt', 'r') as f:
        ids = {line.strip() for line in f}

    # Step 2: Create the SQL query
    ids_str = ', '.join(f"'{id}'" for id in ids)  # Add single quotes around each id
    sql_create = f"CREATE TABLE bad_definitions AS SELECT * FROM us_federal_ecfr WHERE definitions is not Null AND not node_type = 'hub' AND id NOT IN ({ids_str})"

    # Step 3: Execute the query
    conn = util.db_connect(user=)
    cur = conn.cursor()
    cur.execute(sql_create)
    conn.commit()
    cur.close()
    
    
def fix_cases_below_5():
    sql_select = f"SELECT * FROM bad_definitions WHERE node_type IS DISTINCT FROM 'hub' AND (not definitions ? 'scope_ids') AND (definitions ? 'local_definitions') AND (core_metadata ->> 'definition_case' != '5');"
    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    print(len)
    for row in rows:
        print(f"Node ID: {row.id.raw_id}")
        
        if row.level_classifier == "appendix":
            scope_id = row.parent
        else:
            scope_id_temp = row.id.pop_level()
            if "sub" in scope_id_temp.current_level[0]:
                scope_id_temp = scope_id_temp.pop_level()
            scope_id = scope_id_temp.raw_id
        
        print(f"New Scope ID: {scope_id}")
        definitions: DefinitionHub = row.definitions
        definitions.scope_ids = [scope_id]
        if not row.processing:
            row.processing = {}
        row.processing['ready_for_update'] = True
        row.definitions = definitions
        
        util.pydantic_update("bad_definitions", [row], where_field="id", include=None, user=)

def fix_references():
    
    LOGGER.debug("Fixing References")
    
    sql_select = f"SELECT * FROM us_federal_ecfr WHERE node_text is not Null AND (processing is Null OR not processing ? 'updated_references');"
    rows: List[Node] = util.pydantic_select(sql_select, modelType=Node, user=)
    LOGGER.debug(f"Rows Remaining: {len(rows)}")
    
    # 36236 for this batch smh 
    for row in rows:
        LOGGER.debug(f"Node ID: {row.id.raw_id}")

        node_text = row.node_text
        for paragraph_id, paragraph in node_text.paragraphs.items():
            #LOGGER.debug(f"Paragraph ID: {paragraph_id}")
            reference_hub = paragraph.references
            if reference_hub is None:
                continue

            
            for link, reference in reference_hub.references.items():
                #LOGGER.debug(f"Old Reference: {reference}")
                if reference.corpus is not None:
                    #LOGGER.debug(f"Corpus: {reference.corpus}\n")
                    continue

                if "#" in link:
                    temp_link, new_paragraph_id = link.split("#")
                    reference.paragraph_id = new_paragraph_id
                else:
                    temp_link = link
                correct_link, correct_id = analyze_partial_link(temp_link, )
                if correct_link is None:
                    continue
                reference.id = correct_id
                
            
            

                #LOGGER.debug(f"New reference: {reference}\n")
            paragraph.references = reference_hub
        row.node_text = node_text

        addendum = row.addendum
        if addendum is not None:
            if addendum.authority is not None:
                authority_references = addendum.authority.references
                if authority_references is not None:
                    for link, reference in authority_references.references.items():
                        if reference.corpus is not None:
                            continue
                        correct_link, correct_id = analyze_partial_link(link, )
                        if correct_link is None:
                            continue
                        reference.id = correct_id
                addendum.authority.references = authority_references
            if addendum.source is not None:
                source_references = addendum.source.references
                if source_references is not None:
                    for link, reference in source_references.references.items():
                        if reference.corpus is not None:
                            continue
                        correct_link, correct_id = analyze_partial_link(link, )
                        if correct_link is None:
                            continue
                        reference.id = correct_id
                addendum.source.references = source_references
            if addendum.history is not None:
                history_references = addendum.history.references
                if history_references is not None:
                    for link, reference in history_references.references.items():
                        if reference.corpus is not None:
                            continue
                        correct_link, correct_id = analyze_partial_link(link, )
                        if correct_link is None:
                            continue
                        reference.id = correct_id
                addendum.history.references = history_references
            row.addendum = addendum
        if row.processing is None:
            row.processing = {}
        row.processing['updated_references'] = True

        util.pydantic_update("us_federal_ecfr", models=[row], where_field="id",  user=)
        
if __name__ == "__main__":
    main()