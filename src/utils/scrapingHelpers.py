import psycopg
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from urllib.error import URLError
from src.utils import utilityFunctions as util
from src.utils.pydanticModels import Node, NodeID
from bs4 import BeautifulSoup, Tag

from typing import Optional

import requests
from requests.exceptions import HTTPError, ConnectionError
import time
import re
import logging

from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List, Tuple
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

# Set up a basic logger for legacy scrapingHelpers
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
                try:
                    # Remove any old version numbers
                    v_index = new_node_id.index("-v_")
                except:
                    v_index = len(new_node_id)

                    # Tag this node's original in the duplicate's core_metadata
                    if node.core_metadata:
                        node.core_metadata["duplicated_from_node_id"] = node.node_id
                    else:
                        node.core_metadata = {"duplicated_from_node_id": node.node_id}

                new_node_id = new_node_id[0:v_index]
                # Add new version number, starting with 2
                new_node_id += f"-v_{i}"

                if debug_mode:
                    print(f"Adding duplicate version number for: {new_node_id}")
                # Try to insert again
                node.id = NodeID(raw_id=new_node_id)
                continue

            else:
                if debug_mode:
                    print(f"   **Ignoring duplicate")

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
        # 🔍 DELAY DEBUGGING: Legacy scrapingHelpers delay
        if delay_time:
            logger.warning(f"⏰ LEGACY SCRAPING HELPERS DELAY: {delay_time}s")
            time.sleep(delay_time)
        else:
            logger.debug("🚀 LEGACY SCRAPING HELPERS NO DELAY")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response.encoding="utf-8"
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except HTTPError as e:
        print(response.headers)
        print(response.reason)
        print(response.cookies)
        print(f"HTTP Error {e.response.status_code} for URL: {url}")
        exit(1)
        raise e
    except ConnectionError as e:
        print(f"Connection error for URL: {url}")
        print(e)
        raise e
    except Exception as e:
        print(f"An error occurred!")
        print(e)
        raise e


def selenium_elements_present(parent: WebElement, locator, min_elements: int = 1):
    """
    Custom Expected Condition that checks if elements are present within a parent element. Returns false if number of returned elements is less than min_elements.
    """
    def predicate(driver):
        # Check if a disallowed element locator is present, if so return empty
        
        elements = parent.find_elements(*locator)

        if len(elements) < min_elements:
            return False
        
        
        return elements if elements else False

    return predicate

def selenium_element_present(parent: WebElement, locator):
    """
    Custom Expected Condition that checks if an element is present within a parent element.
    """
    def predicate(driver):
        # Attempt to find the elements within the parent and check if they're present
        element = parent.find_element(*locator)
        return element if element else False

    return predicate


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
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text