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

BASE_URL = "https://www.revisor.mn.gov"
TOC_URL = "https://www.revisor.mn.gov/statutes/"

def main():
    pass

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    soup = soup.find(id="toc_table").tbody
    all_rows = soup.find_all("tr")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for row in all_rows:
            all_tds = row.find_all("td")
            link_container = all_tds[0]
            link = link_container.find("a")
            part_container = all_tds[1]
            part = part_container.get_text().strip()
            
            output_link = BASE_URL + link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()


if __name__ == "__main__":
    main()