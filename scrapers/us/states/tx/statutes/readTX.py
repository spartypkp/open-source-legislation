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

BASE_URL = "Website URL with no subpages"
TOC_URL = "https://statutes.capitol.texas.gov/Index.aspx"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    # Get the names of all folders in the DIR/data directory
    # Each folder is a top level title
    all_top_level_titles = []
    for folder in os.listdir(f"{DIR}/data"):
        if "DS_STORE" in folder:
            continue
        print(folder)
        print(folder.split(".")[0])

    with open(f"{DIR}/data/top_level_titles.txt","w") as write_file:
        for folder in os.listdir(f"{DIR}/data"):
            if "DS_STORE" in folder:
                continue
            top_level_title = folder.split(".")[0].strip()
            if top_level_title == "":
                continue
            
            write_file.write(top_level_title + "\n")
            
    write_file.close()


if __name__ == "__main__":
    main()