
import psycopg2

import utilityFunctions as util
from pydanticModels import Node

def insert_jurisdiction_and_corpus_node(country_code: str, jurisdiction_code: str, corpus_code: str) -> Node:
    jurisdiction_model = Node(
        id=f"{country_code}/{jurisdiction_code}",
        node_type="jurisdiction",
        level_classifier="jurisdiction",
        parent=None
    )
    corpus_model = Node(
        id=f"{country_code}/{jurisdiction_code}/{corpus_code}",
        node_type="corpus",
        level_classifier="corpus",
        parent=f"{country_code}/{jurisdiction_code}"
    )
    
    insert_node(jurisdiction_model)
    insert_node(corpus_model, )
    return corpus_model


def insert_node(node: Node, table_name: str, ignore_duplicate=False) -> Node:
    try:
        util.pydantic_insert(table_name, [node])
    except psycopg2.errors.UniqueViolation as e:
        if not ignore_duplicate:
            raise e
    return node
    