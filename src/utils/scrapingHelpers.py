
import psycopg
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from urllib.error import URLError
from src.utils import utilityFunctions as util
from src.utils.pydanticModels import Node
from bs4 import BeautifulSoup

from typing import Optional

import requests
from requests.exceptions import HTTPError, ConnectionError
import time


def insert_jurisdiction_and_corpus_node(country_code: str, jurisdiction_code: str, corpus_code: str) -> Node:
    """
    Creates and inserts jurisdiction and corpus nodes into the specified database tables based on the provided country, jurisdiction, and corpus codes. 
    This function ensures that duplicate entries are ignored.

    Args:
        country_code (str): The country code representing the top-level geographical entity.
        jurisdiction_code (str): The jurisdiction code representing a lower-level geographical entity within the country.
        corpus_code (str): The corpus code representing the collection of documents within the jurisdiction.

    Returns:
        Node: The Pydantic model of the corpus node that was last added to the database. This node can be used for further operations in scrapers.

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


def insert_node(node: Node, table_name: str, ignore_duplicate=False, debug_mode=False) -> Node:
    """
    Inserts a node into a specified database table. Optionally, the function can ignore duplicates based on the `ignore_duplicate` flag. Default behavior is to allow nodes with duplicated IDs, but to add a version tag '-v_n'.

    Args:
        node (Node): The Pydantic model of the node to be inserted into the database.
        table_name (str): The name of the database table where the node is to be inserted.
        ignore_duplicate (bool): If set to True, duplicate node insertions are ignored. If False, duplicates cause a psycopg2 UniqueViolation to be raised.
        debug_mode (bool): If set to True, the function will print debug information about the insertion process.

    Returns:
        Node: The node that was inserted into the database. This is the same node passed in the `node` argument.

    Raises:
        psycopg.errors.UniqueViolation: If a duplicate node insertion is attempted and `ignore_duplicate` is set to False, this error is raised.
    """
    # Loop for allowing duplicate Node's with differing version numbers
    for i in range(2, 10):
        try:
            if debug_mode:
                print(f"-Inserting: {node.node_id}")
            util.pydantic_insert(table_name, [node])
            # Break out if successfully inserted
            break
        except psycopg.errors.UniqueViolation as e:
            if not ignore_duplicate:
                new_node_id = node.node_id
                # Remove any old version numbers
                v_index = new_node_id.find("-v_")
                new_node_id = new_node_id[0:v_index]
                # Add new version number, starting with 2
                new_node_id += f"-v_{i}"

                if debug_mode:
                    print(f"Adding duplicate version number for: {new_node_id}")
                # Try to insert again
                continue

            else:
                if debug_mode:
                    print(f"Ignoring duplicate for: {node.node_id}")

                break
    return node
    

@retry(
    retry=(retry_if_exception_type(HTTPError) | retry_if_exception_type(ConnectionError)),
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5)
)
def get_url_as_soup(url: str, delay_time: Optional[int] = None) -> BeautifulSoup:
    """
    Fetches the contents of a URL and returns it as a BeautifulSoup object.

    Args:
        url (str): The URL to fetch.
        delay_time Optional(int): Number of seconds to delay to mimic human browsing.

    Returns:
        BeautifulSoup: Parsed HTML content of the page.

    Raises:
        HTTPError: If an HTTP error occurs (4xx, 5xx).
        ConnectionError: If a connection error occurs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        # Introduce a small delay to mimic human browsing
        if delay_time:
            time.sleep(delay_time)
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except HTTPError as e:
        print(f"HTTP Error {e.response.status_code} for URL: {url}")
        raise e
    except ConnectionError as e:
        print(f"Connection error for URL: {url}")
        raise e
    except Exception as e:
        print(f"An error occurred!")
        raise e
        