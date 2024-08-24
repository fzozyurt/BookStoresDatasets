import json
import logging
import os
from bs4 import BeautifulSoup
import numpy as np

from Selenium import initialize_driver

# Configure logging
from additional import log_config
log_config(os.getenv('LOG_FILE'))

def scrape_categories():
    logging.info('scrape_categories function called')
    links = []

    # Importing categories
    url = "https://www.kitapyurdu.com/index.php?route=product/category"
    logging.info(f'URL: {url}')

    wd = initialize_driver()
    wd.get(url)
    html_content = wd.page_source
    soup = BeautifulSoup(html_content, "html.parser")
    categories = soup.find_all("a", class_=["category-item"])
    for a in range(len(categories)):
        link_info = {'name': categories[a].text.strip(), 'url': str((categories[a]['href']))}
        links.append(link_info)
        logging.info(f'Category found: {link_info}')

    data_partitioning(links)
    logging.info('scrape_categories function completed')

def data_partitioning(links):
    logging.info('data_partitioning function called')
    # Convert data to numpy array and shuffle
    data_array = np.array(links)
    np.random.shuffle(data_array)
    logging.info('Data shuffled')

    # Split data into 5 parts
    split_data = np.array_split(data_array, 5)
    logging.info('Data split into 5 parts')

    # Write each part to separate JSON files
    for i, chunk in enumerate(split_data):
        file_name = f'categories_{i + 1}.json'
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(chunk.tolist(), file, ensure_ascii=False, indent=4)
        logging.info(f'Written to file: {file_name}')

    logging.info('data_partitioning function completed')

if __name__ == "__main__":
    scrape_categories()
    logging.shutdown()