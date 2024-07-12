import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utils.utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import json
from bs4.element import Tag

BASE_URL = "https://www.capitol.hawaii.gov"
TOC_URL = "https://www.capitol.hawaii.gov/docs/hrs.htm"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)
    time.sleep(5)

    
    soup = BeautifulSoup(DRIVER.page_source, features="html.parser")
    

    
    all_links = soup.find_all("a")
    set_of_links = set()
    for i, link in enumerate(all_links):
        output_link = link['href'] + "\n"
        set_of_links.add(output_link)
    print(len(set_of_links))
    list_of_links = list(set_of_links)
    list_of_links.sort()

        
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in list_of_links:
            write_file.write(link)
    write_file.close()


if __name__ == "__main__":
    main()