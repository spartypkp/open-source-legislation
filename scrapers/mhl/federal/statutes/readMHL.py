from bs4 import BeautifulSoup, NavigableString
from selenium import webdriver
from selenium.webdriver.common.by import By

import urllib.parse 
from urllib.parse import unquote, quote
import urllib.request
import requests
import json
import time
import re
import urllib.request
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from urllib.error import URLError
from pypdf import PdfReader
import psycopg2
import os
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util

TOC_URL = "https://rmiparliament.org/cms/legislation.html"
BASE_URL = "https://rmiparliament.org"


def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    driver = webdriver.Chrome()
    driver.get(TOC_URL)
    driver.implicitly_wait(0.5)
    
    with open(f"{DIR}/data/top_level_titles.txt", "w") as write_file:
        for i in range(0, 26):
            # No laws for Q, X, Z
            if i == 16 or i == 23 or i == 25:
                continue
            submit_buttons = driver.find_elements(by=By.NAME, value="submit4")
            submit_button = submit_buttons[i]
            submit_button.click()

            
            html = driver.page_source
            soup = BeautifulSoup(html)

            table = soup.find(class_ = "table table-bordered table-hover table-condensed")
            table_body = table.tbody
            
            for i, tr in enumerate(table_body.find_all('tr', recursive=False)):
                #print(tr)
                all_tds = tr.find_all(recursive=False)
                pdf_element = all_tds[3]
                #print(pdf_element)
                pdf_link_element = pdf_element.find("a")
                pdf_link = BASE_URL + pdf_link_element['href']
                pdf_name = pdf_link.split("/")[-1]
                write_file.write(pdf_name + "\n")
                write_file.write(pdf_link + "\n")
                save_pdf_file(pdf_link, pdf_name)

            
            
    write_file.close()

def save_pdf_file(pdf_url, pdf_name):
    
    # Send an HTTP GET request to the PDF URL
    response = requests.get(pdf_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Get the content of the PDF
        pdf_content = response.content

        # Save the PDF content to the local file
        with open(f"{DIR}/data/{pdf_name}", 'wb') as pdf_file:
            pdf_file.write(pdf_content)

        print(f"{pdf_name} successfully downloaded.")
    else:
        print(f"Failed to download PDF (Status Code: {response.status_code})")

if __name__ == "__main__":
    main()


