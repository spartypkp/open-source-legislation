
import psycopg

from src.utils import utilityFunctions as util
from src.utils.pydanticModels import Node

def insert_jurisdiction_and_corpus_node(country_code: str, jurisdiction_code: str, corpus_code: str) -> Node:
    """
    Inserts the  jurisdiction, and corpus node in order for a given jurisdiction. By default, ignores any duplicates. Returns the last added node (corpus) for use in scrapers.
    """

    jurisdiction_model = Node(
        id=f"{country_code}/{jurisdiction_code}",
        node_type="structure",
        level_classifier="jurisdiction"
    )
    corpus_model = Node(
        id=f"{country_code}/{jurisdiction_code}/{corpus_code}",
        node_type="structure",
        level_classifier="corpus",
        parent=f"{country_code}/{jurisdiction_code}"
    )
    table_name = f"{country_code}_{jurisdiction_code}_{corpus_code}"
    
    insert_node(node=jurisdiction_model, table_name=table_name, ignore_duplicate=True)
    insert_node(node=corpus_model, table_name=table_name, ignore_duplicate=True )
    return corpus_model


def insert_node(node: Node, table_name: str, ignore_duplicate=False) -> Node:
    """
    Insert a node into a table. If ignore_duplicate is False and a psycopg2 UniqueViolate occurs, it will be raised. Otherwise it will be ignored.
    """
    try:
        util.pydantic_insert(table_name, [node])
    except psycopg.errors.UniqueViolation as e:
        if not ignore_duplicate:
            raise e
        print(f"Ignoring duplicate for: {node.node_id}")
    return node
    