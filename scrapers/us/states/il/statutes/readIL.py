from bs4 import BeautifulSoup
import urllib.request
import requests
import json
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

BASE_URL = "https://www.ilga.gov/legislation/ilcs/"
TOC_URL = "https://www.ilga.gov/legislation/ilcs/ilcs.asp"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="toplinks")
    link_container = soup.find("ul")
    all_links = link_container.find_all("a")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            output_link = BASE_URL + link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()


if __name__ == "__main__":
    main()