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

BASE_URL = "https://le.utah.gov/xcode/"
TOC_URL = "https://le.utah.gov/xcode/code.html"

def main():
    read_all_top_level_titles_soup()

# FULL SELENIUM WAY
def read_all_top_level_titles_selenium():
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)

    # Find container of all titles
    titles_container = DRIVER.find_element(By.ID, "childtbl")
    # Iterate over all titles
    all_links = titles_container.find_elements(By.TAG_NAME, "a")
    
    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            href = link.get_attribute('href')
            output_link = href + "\n"
            write_file.write(output_link)
    write_file.close()


# ONLY USE SELENIUM TO LOAD THE PAGE
def read_all_top_level_titles_soup():
    DRIVER = webdriver.Chrome()
    DRIVER.get(TOC_URL)
    DRIVER.implicitly_wait(.25)

    # Find container of all titles
    titles_container = DRIVER.find_element(By.ID, "childtbl")
    
    titles_container_soup = BeautifulSoup(titles_container.get_attribute("outerHTML"), features="html.parser")
    all_links = titles_container_soup.find_all("a")

    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for link in all_links:
            output_link = BASE_URL + link['href'] + "\n"
            write_file.write(output_link)
    write_file.close()







if __name__ == "__main__":
    main()