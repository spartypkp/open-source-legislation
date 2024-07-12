from bs4 import BeautifulSoup, NavigableString
import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
import requests
import json
import re
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

BASE_URL = "https://www.faa.gov/"
TOC_URL = "https://www.faa.gov/air_traffic/publications/atpubs/aim_html/"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find(class_="book-summary aip-index")
    all_title_containers = soup.find_all(recursive=False)

    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for title_container in all_title_containers:
            link = title_container.find("a")
            output_link = TOC_URL + link['href'].strip() + "\n"
            all_text = title_container.get_text().strip() + "\n"
            write_file.write(all_text)
            write_file.write(output_link)
    write_file.close()


if __name__ == "__main__":
    main()