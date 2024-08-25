import json
import logging
import os
from bs4 import BeautifulSoup
import numpy as np

from Selenium import initialize_driver
from additional import data_partitioning, log_config

log_config("KY.LOG")

def scrape_categories():
    logging.info('scrape_categories function called')
    links = []
    site = 'https://www.bkmkitap.com'
    logging.info("Starting to scrape categories from %s", site)
    url = "https://www.bkmkitap.com/kategori-listesi"
    try:
        wd = initialize_driver()
        wd.get(url)
        html_content = wd.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        categories = soup.find_all("a", class_=["category-item"])
        for a in range(len(categories)):
            link_info = {'name': categories[a].text.strip(), 'url': str((categories[a]['href']))}
            links.append(link_info)
            logging.info(f'Category found: {link_info}')
        wd.quit()
        logging.debug('Web driver closed successfully')
    except Exception as e:
        logging.error(f'Error scraping categories: {e}')
        if wd:
            wd.quit()
            logging.debug('Web driver closed after error')

    data_partitioning(links)
    logging.info('data_partitioning function completed')

if __name__ == "__main__":
    scrape_categories()
    logging.shutdown()