import json
import logging
import os
from bs4 import BeautifulSoup
import requests
import math
import numpy as np

from additional import log_config,data_partitioning


log_config(os.getenv('LOG_FILE'))

def scrape_categories():
    links = []
    site = 'https://www.bkmkitap.com'
    logging.info("Starting to scrape categories from %s", site)

    # Kategori İçe Aktarma
    url = "https://www.bkmkitap.com/kategori-listesi"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info("Successfully fetched the category list from %s", url)
    except requests.RequestException as e:
        logging.error("Error fetching the category list: %s", str(e))
        return

    html_icerigi = response.content
    soup = BeautifulSoup(html_icerigi, "html.parser")
    kategori=soup.find_all("a", class_=["w-100 d-block block-title"])
    for a in range(len(kategori)):
        link = {'name': str(kategori[a].text), 'url': str(site + "" + (kategori[a]['href'])+'?&stock=1')}
        links.append(link)
        logging.debug("Found category: %s", link)

    data_partitioning(links)


if __name__ == "__main__":
    scrape_categories()
    logging.shutdown()