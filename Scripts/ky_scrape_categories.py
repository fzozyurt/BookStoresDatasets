import logging
import os
from bs4 import BeautifulSoup
import requests
import numpy as np

from additional import log_config,data_partitioning


log_config(os.getenv('LOG_FILE'))

headers = {
    'User-Agent': 'Chrome/91.0.4472.124',
    'Accept': 'text/html'
}

def scrape_categories():
    links = []
    site = 'https://www.kitapyurdu.com'
    logging.info("Starting to scrape categories from %s", site)

    # Kategori İçe Aktarma
    url = "https://www.kitapyurdu.com/index.php?route=product/category"
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            logging.info("Successfully fetched the category list from %s", url)
        else:
            logging.error(f"Failed to fetch the category list from {url} - Response Status: {response.status_code}")
            return
    except requests.RequestException as e:
        logging.error("Error fetching the category list: %s", str(e))
        return

    html_icerigi = response.content
    soup = BeautifulSoup(html_icerigi, "html.parser")
    kategori=soup.find_all("div", class_="category")
    for a in range(len(kategori)):
        link = {'name': str(kategori[a].find("h2").text), 'url': str(kategori[1].find("a", class_="category-item")["href"])}
        links.append(link)
        logging.debug("Found category: %s", link)

    data_partitioning(links)


if __name__ == "__main__":
    scrape_categories()
    logging.shutdown()