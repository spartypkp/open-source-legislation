import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from processingHelpers import generate_embedding_for_row, generate_embeddings_in_batch, read_rows_sequentially, update_rows_in_batch


TABLE_NAME = "aim_node"



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
        update_rows_in_batch(updated_rows, TABLE_NAME)
        
        #print(updated_rows[0])
    
    print("Total rows read: ", TOTAL_ROWS_READ)
    print("Total rows updated: ", TOTAL_ROWS_UPDATED)
    return







if __name__ == "__main__":
    main()