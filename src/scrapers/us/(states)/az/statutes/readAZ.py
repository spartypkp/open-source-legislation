from bs4 import BeautifulSoup

from urllib.request import Request, urlopen
import os
import sys
import json
DIR = os.path.dirname(os.path.realpath(__file__))


BASE_URL = "https://www.azleg.gov"
TOC_URL = "https://www.azleg.gov/arstitle/"

def main():
    read_all_top_level_titles()

def read_all_top_level_titles():
    """
    Go to the TOC URL and get the individual page links for each top level title.
    """
    
    req = Request(
        url=TOC_URL, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    webpage = urlopen(req).read()
    text = webpage.decode('utf-8') # a `str`; 
    soup = BeautifulSoup(text, features="html.parser")

    soup = soup.find(id="arsTable")
    all_links = soup.find_all("a")

    top_level_title_links = []
    for link in all_links:
        top_level_title_links.append(link['href'])
    
    output_json = json.dumps({"top_level_titles": top_level_title_links})

    with open(f"{DIR}/top_level_title_links.json","w") as write_file:
        write_file.write(output_json)
    write_file.close()


if __name__ == "__main__":
    main()