import json
import psycopg2
import psycopg2.extras
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from utils.pydanticModels import Node, NodeID, NodeText, Paragraph, Definition, DefinitionHub, IncorporatedTerms, Reference, ReferenceHub, AddendumType, Addendum
from typing import List, Union, Any

import concurrent.futures

TABLE_NAME = "us_federal_ecfr"
BATCH_SIZE = 1000
="will2"


def main():
    #test_creation()
    TOTAL_ROWS_READ = 0
    TOTAL_ROWS_UPDATED = 0

    while True:
        rows = read_rows_sequentially()
        if (rows is None or len(rows) == 0):
            break
        TOTAL_ROWS_READ += len(rows)
        updated_rows = generate_embeddings_in_batch(rows)
        TOTAL_ROWS_UPDATED += len(rows)
        print(f"Rows updated: ", TOTAL_ROWS_UPDATED)
        
        update_rows_in_batch(updated_rows)
        
        
        
    #     #print(updated_rows[0])
    
    # print("Total rows read: ", TOTAL_ROWS_READ)
    # print("Total rows updated: ", TOTAL_ROWS_UPDATED)
    # return

def test_creation():
    
    sql_select = f"SELECT * FROM us_federal_ecfr WHERE id = 'us/federal/ecfr/title=1/chapter=I/subchapter=D/part=12/section=12.1';"
    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    
    print(f"Node ID: {rows[0].node_id}")
    first_row: Node = rows[0]
    node_text: NodeText = first_row.node_text
    paragraphs = node_text.to_tree()
    
    with open("testParagraphs.json", "w") as file:
        file.write(json.dumps(paragraphs))
    file.close()

def fix_unknown_terms():
    sql_select = f"SELECT * FROM us_federal_ecfr WHERE definitions is not null and definitions -> 'local_definitions' ? 'UNKNOWN';"
    rows: List[Node] = util.pydantic_select(sql_select, classType=Node, user=)
    for row in rows:
        definitions = row.definitions
        local_definitions = definitions.local_definitions
        new_scope = local_definitions["UNKNOWN"].definition
        del local_definitions["UNKNOWN"]
        definitions.scope = new_scope
        definitions.local_definitions = local_definitions

        util.pydantic_update("us_federal_ecfr", [row], where_field='id', include=None, user=)


# TEXT, TEXT, VECTOR, JSON
# [(node_id, node_text, node_text_embedding, node_tags)]
def generate_embedding_for_row(row: Node) -> Node:
    # row is a tuple
    node_embedding = None  
    try:
        text = '\n'.join(row.node_text.to_list_text())
        node_embedding = util.create_embedding(text)
       
    except Exception as e:
        print("Failed embedding!", e)
        node_embedding = None
    
    row.text_embedding = node_embedding
    return row

def generate_embeddings_in_batch(rows, max_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map the generate_embedding_for_row function to each row
        future_to_row = {executor.submit(generate_embedding_for_row, row): row for row in rows}
        
        updated_rows: List[Node] = []
        for future in concurrent.futures.as_completed(future_to_row):
            row = future_to_row[future]
            try:
                updated_row = future.result()
                #print(f"Updated row: ", updated_row)
                updated_rows.append(updated_row)
            except Exception as exc:
                print(f'Row {row[0]} generated an exception: {exc}')
        
        return updated_rows


def read_rows_sequentially() -> List[Node]:
    try:
        
        sql_logic = f"""
            SELECT * FROM {TABLE_NAME}
            WHERE node_text IS NOT NULL 
            AND text_embedding IS NULL
            AND (core_metadata ->> 'tokens')::integer < 8000
            ORDER BY id
            LIMIT {BATCH_SIZE};
        """
        rows: List[Node] = util.pydantic_select(sql_logic, Node, )
        return rows
        
    except psycopg2.Error as error:
        print(f"Error fetching data from table {TABLE_NAME}: {error}")
        return None

def update_rows_in_batch(processed_rows: List[Node]):
    """
    Update the node_text_embedding and node_tags fields in the database in a batch.
    processed_rows: List of tuples containing the updated node_text_embedding data, node_tags data, and the corresponding node_id
    """
    
    
    try:
        
        # Prepare your SQL statement for updating the node_text_embedding and node_tags fields
        
        util.pydantic_update(TABLE_NAME, , processed_rows, where_field='id', update_columns=['text_embedding', 'id'])

        # Execute the batch update

    except psycopg2.Error as error:
        
        print(f"Error updating data in table {TABLE_NAME}: {error}")
        




    


def example():
    # Start using OpenAI chat completion
    actual_data = "blahblahblah"
    system = "You are a helpful legal research assistant who specializes in extracting key information from semi-structured text.\n\nYou will be given some text which denotes a Table of Contents of some legislation. This legislation was converted from a PDF to a text file and therefore has some minor formatting errors.\n\nYou will assist a researcher by extracting some key information from the Table of Contents page, following these instructions:\n1. Extract the Title this legislation is organized under. This will almost always be near the top of the page and be in the format \"TITLE # - NAME\". Extract separately the title number and title name into variables called \"title_num\" and \"title_name\".\n2. Extract the Chapter this legislation is directly contained under. The Chapter is a further way of organizing legislation. Chapters belong to a title, which you have already found. Chapter information will be in the format \"CHAPTER # - NAME\". Extract separately the chapter number and chapter name into variables called \"chapter_num\" and \"chapter_name\".\n3. Extract the page number of the first section listed. You want to let the researcher know on which page the actual legislative text of sections occurs. The table of contents will contain lists of sections, their names, and a page number to find it on. This will appear in this format \"§201.  Short title.  ................................ ................................ ................................ ..............................  3 \". We only want to find the first page of the first section. Section is denoted by \"§\". Return the page number (3 in this case) in the variable \"section_page_number\".\n4. Before returning your extracted variables, check and correct minor spelling and punctuation errors.\n\nReturn your variables in json format."
     = f"{actual_data}"
    messages = util.convert_to_messages(system, )
    params = util.get_chat_completion_params("gpt-3.5-turbo-16k", messages, 0.4, 4000)
    response_raw = util.create_chat_completion(params)
    response = json.loads(response_raw)
    print(response)
    return response

if __name__ == "__main__":
    main()

