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

BASE_URL = "https://docs.legis.wisconsin.gov/statutes/statutes/"
TOC_URL = "https://docs.legis.wisconsin.gov/statutes/statutes"

def main():
    TOC_URL = "https://docs.legis.wisconsin.gov/statutes/statutes"
    read_all_top_level_titles(TOC_URL)

def read_all_top_level_titles(TOC_URL):
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find("ul", class_="docLinks")
    all_links = soup.find_all("a")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            if (".pdf" in link['href']):
                continue
            href = link['href'].split('/')
            number = href[-1]
            output_link = BASE_URL +  number + "\n"
            write_file.write(output_link)
    write_file.close()


if __name__ == "__main__":
    main()