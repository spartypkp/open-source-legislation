from bs4 import BeautifulSoup
import urllib.request
import requests
import json
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util

BASE_URL = "https://delcode.delaware.gov/"
TOC_URL = "https://delcode.delaware.gov/"

def main():
    pass

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find(id="content")
    print(soup)
    html_links = soup.find_all("div", class_="title-links")
    print(html_links)
    for link in html_links:
        first_atag = link.find_all("a")
        if (".html" in first_atag['href']):
            with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
                output_link = BASE_URL + first_atag['href'] + "\n"
                write_file.write(output_link)
            write_file.close()


if __name__ == "__main__":
    main()