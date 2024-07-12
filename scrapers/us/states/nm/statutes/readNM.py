from bs4 import BeautifulSoup
import urllib.request
import requests
import json
import os
import psycopg2
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

BASE_URL = "https://nmonesource.com"
TOC_URL = "https://nmonesource.com/nmos/nmsa/en/nav_date.do?page="
TABLE_NAME = "nm_node"
 = "will2"

def main():
    insert_jurisdiction_and_corpus_node()
    read_all_top_level_titles()

def read_all_top_level_titles():
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for i in range(1, 5):
            actual_url = TOC_URL + str(i)
            print( actual_url)
            response = urllib.request.urlopen(actual_url)
            data = response.read()      # a `bytes` object
            text = data.decode('utf-8') # a `str`; 
            soup = BeautifulSoup(text, features="html.parser")
            soup = soup.find(id="decisia-iframe")
            iframe_response = requests.get(BASE_URL + soup["src"])
            soup = BeautifulSoup(iframe_response.text, 'html.parser')
            
            soup = soup.find(class_="collectionItemList list-expanded")
            
            
            
            node_parent = "nm/statutes/"
            all_chapters = soup.find_all(recursive=False)
            
            for chap in all_chapters:
                data = chap.find(class_="info")
                node_name = data.h3.get_text()
                node_number = node_name.split(" ")[1]
                node_level_classifier = "chapter"
                node_type = "structure"
                node_id = f"nm/statutes/{node_level_classifier.upper()}={node_number}/"
                node_text, node_citation, node_addendum, node_references, node_tags = None, None, None, None, None
                node_link = BASE_URL + data.find("a")["href"]
                write_file.write(node_link + "\n")
                node_data = (node_id, node_number, node_type, node_level_classifier, node_text, None, node_citation, node_link, node_addendum, node_name, None, None, None, None, None, node_parent, None, None, node_references, None, node_tags)
                insert_node_ignore_duplicate(node_data)

    write_file.close()



def insert_jurisdiction_and_corpus_node():
    jurisdiction_row_data = (
        "nm/",
        None,
        "jurisdiction",
        "STATE",
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
        "nm/statutes/",
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
        "nm/",
        None,
        None,
        None,
        None,
        None,
    )
    util.insert_row_to_local_db(, TABLE_NAME, jurisdiction_row_data)
    util.insert_row_to_local_db(, TABLE_NAME, corpus_row_data)








if __name__ == "__main__":
    main()