
import psycopg
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import urllib.request
from urllib.error import URLError
from src.utils import utilityFunctions as util
from src.utils.pydanticModels import Node
from bs4 import BeautifulSoup

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
    

@retry(
    retry=retry_if_exception_type(URLError),       # Retry on URLError
    wait=wait_exponential(multiplier=1, max=60),   # Exponential backoff with a max wait of 60 seconds
    stop=stop_after_attempt(5)                     # Stop after 5 attempts
)
def get_url_as_soup(url: str) -> BeautifulSoup:
    """
    Given a string url, try to connect to the url, read the page, and convert to a BeautifulSoup object
    """
    try:
        # Attempt to open the URL
        response = urllib.request.urlopen(url)
        data = response.read()      # a `bytes` object
        text = data.decode('utf-8') # a `str`; 
        soup = BeautifulSoup(text, 'html.parser')
        return soup

    except Exception as e:
        # Not sure what I want to do with this for now!
        raise e