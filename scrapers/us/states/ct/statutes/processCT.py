import json
import psycopg2
import psycopg2.extras
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

import concurrent.futures

TABLE_NAME = "ct_node"
BATCH_SIZE = 1000
="will"


def main():
    TOTAL_ROWS_READ = 0
    TOTAL_ROWS_UPDATED = 0

    while True:
        rows = read_rows_sequentially()
        if (rows is None or len(rows) == 0):
            break
        TOTAL_ROWS_READ += len(rows)
        updated_rows = generate_embeddings_in_batch(rows)
        TOTAL_ROWS_UPDATED += len(rows)
        update_rows_in_batch(updated_rows)
        
        
        #print(updated_rows[0])
    
    print("Total rows read: ", TOTAL_ROWS_READ)
    print("Total rows updated: ", TOTAL_ROWS_UPDATED)
    return



# TEXT, TEXT, VECTOR, JSON
# [(node_id, node_text, node_text_embedding, node_tags)]
def generate_embedding_for_row(row):
    # row is a tuple
    node_id = row[0]   
    node_embedding = None  
    node_tags = row[3]
    try:
        text = "\n".join(row[1])
        node_embedding = util.create_embedding(text)
       
    except Exception as e:
        print("Failed embedding!", e)
        if (node_tags is None):
            node_tags = {}
        node_tags["failed_embedding"] = True
        node_embedding = None
    
    node_tags = json.dumps(node_tags)
    return (node_embedding, node_tags, node_id)

def generate_embeddings_in_batch(rows, max_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map the generate_embedding_for_row function to each row
        future_to_row = {executor.submit(generate_embedding_for_row, row): row for row in rows}
        
        updated_rows = []
        for future in concurrent.futures.as_completed(future_to_row):
            row = future_to_row[future]
            try:
                updated_row = future.result()
                #print(f"Updated row: ", updated_row)
                updated_rows.append(updated_row)
            except Exception as exc:
                print(f'Row {row[0]} generated an exception: {exc}')
        
        return updated_rows


def read_rows_sequentially():
    try:
        connection = util.psql_connect()
        cursor = connection.cursor()
        sql_logic = f"""
            SELECT node_id, node_text, node_text_embedding, node_tags FROM {TABLE_NAME}
            WHERE node_text IS NOT NULL 
            AND node_text_embedding IS NULL
            AND (node_tags IS NULL OR NOT (node_tags ? 'failed_embedding'))
            ORDER BY node_order
            LIMIT {BATCH_SIZE};
        """
        cursor.execute(sql_logic)
        rows = cursor.fetchall()
        #print(rows)
        cursor.close()
        connection.close()
        return rows
        
    except psycopg2.Error as error:
        print(f"Error fetching data from table {TABLE_NAME}: {error}")
        return None

def update_rows_in_batch(processed_rows):
    """
    Update the node_text_embedding and node_tags fields in the database in a batch.
    processed_rows: List of tuples containing the updated node_text_embedding data, node_tags data, and the corresponding node_id
    """
    for row in processed_rows:
        print(f"Row: (id={row[2]}, tags={row[1]}, embedding is null={row[0] is None})")
    
    try:
        connection = util.psql_connect()
        cursor = connection.cursor()
        # Prepare your SQL statement for updating the node_text_embedding and node_tags fields
        update_query = f"UPDATE {TABLE_NAME} SET node_text_embedding = %s, node_tags = %s WHERE node_id = %s"

        # Execute the batch update
        cursor.executemany(update_query, processed_rows)
        connection.commit()
        print("Committed batch!")
        cursor.close()
        connection.close()

    except psycopg2.Error as error:
        
        print(f"Error updating data in table {TABLE_NAME}: {error}")
        exit(1)
        connection.rollback()



def example_completion():
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

