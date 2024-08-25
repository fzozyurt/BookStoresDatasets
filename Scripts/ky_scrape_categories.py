import logging
import numpy as np
import json
from bs4 import BeautifulSoup
from selenium import webdriver

def scrape_categories(url):
    logging.info('scrape_categories function called')
    links = []
    try:
        wd = webdriver.Chrome()
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
    logging.info('scrape_categories function completed')

def data_partitioning(links):
    logging.info('data_partitioning function called')
    try:
        # Convert data to numpy array and shuffle
        data_array = np.array(links)
        np.random.shuffle(data_array)
        logging.debug('Data shuffled')

        # Split data into 5 parts
        split_data = np.array_split(data_array, 5)
        logging.debug('Data split into 5 parts')

        # Write each part to separate JSON files
        for i, chunk in enumerate(split_data):
            file_name = f'categories_{i + 1}.json'
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(chunk.tolist(), file, ensure_ascii=False, indent=4)
            logging.info(f'Written to file: {file_name}')
    except Exception as e:
        logging.error(f'Error in data partitioning: {e}')