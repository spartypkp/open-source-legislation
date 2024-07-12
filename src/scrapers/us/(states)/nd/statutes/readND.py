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

BASE_URL = "https://www.ndlegis.gov"
TOC_URL = "https://www.ndlegis.gov/general-information/north-dakota-century-code/classic.html"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    response = urllib.request.urlopen(TOC_URL)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text)

    with open(f"{DIR}/data/top_level_titles.txt","a") as write_file:
        soup = soup.find(class_="clearfix text-formatted field field--name-field-pwv-custom-content field--type-text-long field--label-hidden field__item")
        
        for link in soup.find_all("a"):
            output_link = BASE_URL + link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()
                    
        



if __name__ == "__main__":
    main()