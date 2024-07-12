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

BASE_URL = "https://www.ncleg.gov"
TOC_URL = "https://www.ncleg.gov/Laws/GeneralStatutesTOC"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="gsTOC")

    all_links = soup.find_all(class_="row")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            for a in link.find_all("a"):
                if(".html" not in a['href']):
                    continue
                output_link = BASE_URL + a['href'] + "\n"
                write_file.write(output_link)
            
    write_file.close()


if __name__ == "__main__":
    main()