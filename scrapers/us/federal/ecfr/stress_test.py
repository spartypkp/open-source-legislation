import psycopg2
import os
import urllib.request
from bs4 import BeautifulSoup
import sys
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)
import utilityFunctions as util
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import re
import time
import json
from bs4.element import Tag
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By

URL = "https://www.instantdb.com/"

def main():
    with ThreadPoolExecutor(max_workers=10) as executor:
        for _ in range(10):
            executor.submit(click_buttons)
            
    
def click_buttons():
    DRIVER = webdriver.Chrome()
    DRIVER.get(URL)
    DRIVER.implicitly_wait(.25)

    div = DRIVER.find_element(By.CLASS_NAME, "inline-flex.select-none.gap-6.rounded-xl.border.bg-white.p-6.shadow-lg")
    all_buttons = div.find_elements(By.TAG_NAME, "button")
    for i in range(1000000):
        for button in all_buttons:
            button.click()
            


if __name__ == "__main__":
    main()