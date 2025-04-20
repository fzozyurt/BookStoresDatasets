#!/usr/bin/env python3
import os
import json
import logging
import numpy as np
import sys
import argparse

# Import modül yolunu düzenleme
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts.scrapers.ky_scraper import KitapYurduScraper
from Scripts.scrapers.bkm_scraper import BkmKitapScraper


def partition_categories(categories, parts=5, output_dir='.'):
    """
    Partition categories into equal parts and save to JSON files
    """
    # Convert categories to numpy array for shuffling
    data_array = np.array(categories)
    np.random.shuffle(data_array)
    logging.debug("Data shuffled")
    
    # Split into parts
    split_data = np.array_split(data_array, parts)
    logging.info(f"Data split into {parts} parts")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write each part to a JSON file
    for i, chunk in enumerate(split_data):
        file_name = os.path.join(output_dir, f'categories_{i + 1}.json')
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(chunk.tolist(), file, ensure_ascii=False, indent=4)
            logging.info(f"Successfully wrote data to {file_name}")
        except IOError as e:
            logging.error(f"Error writing data to {file_name}: {str(e)}")


def scrape_categories(site_name, parts=5, output_dir='Categories'):
    """
    Scrape categories from a specified site and partition them
    """
    logging.info(f"Starting to scrape {site_name} categories")
    
    if site_name.upper() == "KY":
        scraper = KitapYurduScraper()
        categories = scraper.scrape_categories()
    elif site_name.upper() == "BKM":
        scraper = BkmKitapScraper()
        categories = scraper.scrape_categories()
    else:
        logging.error(f"Unknown site name: {site_name}")
        return False
        
    if categories:
        # Also save all categories to a single file for reference
        all_categories_file = os.path.join(output_dir, f"{site_name}_categories.json")
        try:
            with open(all_categories_file, 'w', encoding='utf-8') as file:
                json.dump(categories, file, ensure_ascii=False, indent=4)
            logging.info(f"Saved all categories to {all_categories_file}")
        except Exception as e:
            logging.error(f"Error saving all categories: {e}")
        
        # Partition categories
        partition_categories(categories, parts, output_dir)
        logging.info(f"Successfully scraped and partitioned {len(categories)} categories from {site_name}")
        return True
    else:
        logging.error(f"No categories found for {site_name}")
        return False


if __name__ == "__main__":
    from Scripts.additional import log_config
    
    parser = argparse.ArgumentParser(description='Scrape categories from specified site.')
    parser.add_argument('site', choices=['KY', 'BKM'], help='Site to scrape categories from (KY or BKM)')
    parser.add_argument('--parts', type=int, default=5, help='Number of parts to split categories into')
    parser.add_argument('--output-dir', type=str, default='Categories', help='Directory to output JSON files')
    parser.add_argument('--log-file', type=str, default='category_scrape.log', help='Log file path')
    
    args = parser.parse_args()
    
    log_config(args.log_file)
    
    scrape_categories(args.site, args.parts, args.output_dir)