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

BASE_URL = "https://code.wvlegislature.gov/"
TOC_URL = "https://code.wvlegislature.gov/"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        container = soup.find(id="sel-chapter")
        for option in container.find_all("option"):
            output_link = BASE_URL + option['value']+ '/' + "\n"
            write_file.write(output_link)
            node_name = option.get_text() + "\n"
            write_file.write(node_name)
    write_file.close()
        
    


if __name__ == "__main__":
    main()