import psycopg2
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

 = "WILL OR WILL2 OR MADELINE"
TABLE_NAME = "JURISDICTION_NODE"



def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "ar/",
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




    