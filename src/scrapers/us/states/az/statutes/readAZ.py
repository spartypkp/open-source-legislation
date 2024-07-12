from bs4 import BeautifulSoup
import urllib.request
from urllib.request import Request, urlopen
import requests
import json
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

BASE_URL = "https://www.azleg.gov"
TOC_URL = "https://www.azleg.gov/arstitle/"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    
    req = Request(
        url=TOC_URL, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    webpage = urlopen(req).read()
    text = webpage.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="arsTable")
    all_links = soup.find_all("a")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            output_link = link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()


if __name__ == "__main__":
    main()