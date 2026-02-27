#!/usr/bin/env python3
import os
import sys
import logging
import argparse

# Modül import yolunu düzenleme
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts.scrapers.ky_scraper import KitapYurduScraper
from Scripts.scrapers.bkm_scraper import BkmKitapScraper
from Scripts.logging_utils import setup_logging


def main():
    """
    Main entry point for running scrapers
    """
    parser = argparse.ArgumentParser(description='Run a specific scraper')
    parser.add_argument('site', choices=['KY', 'BKM'], 
                        help='Site to scrape (KY for Kitap Yurdu, BKM for BKM Kitap)')
    parser.add_argument('--matrix-id', type=str, 
                        help='Matrix ID for parallel processing')
    parser.add_argument('--workers', type=int, default=5, 
                        help='Number of worker threads')
    parser.add_argument('--log-file', type=str, 
                        help='Log file path')
    parser.add_argument('--categories-file', type=str, 
                        help='Categories file path')
    
    args = parser.parse_args()
    
    # Set environment variables if not already set
    if args.matrix_id:
        os.environ['matrix_id'] = args.matrix_id
    if args.log_file:
        os.environ['CLUSTER_LOG_FILE'] = args.log_file
    if args.categories_file:
        os.environ['categories_file'] = args.categories_file
    
    # Ensure matrix_id is set
    matrix_id = os.getenv('matrix_id')
    if not matrix_id:
        print("ERROR: matrix_id is not set. Use --matrix-id argument or set matrix_id environment variable")
        sys.exit(1)
    
    # Ensure categories_file is set
    categories_file = os.getenv('categories_file')
    if not categories_file:
        # Set default if not specified
        os.environ['categories_file'] = f"Categories/categories_{matrix_id}.json"
        print(f"Using default categories file: {os.environ['categories_file']}")
        
    # Fix for log path issue - log_config adds "./logs/" to file name
    # so just pass the base file name without any path
    log_file = args.log_file or f"{args.site}_{matrix_id}.log"
    if '/' in log_file:
        log_file = os.path.basename(log_file)  # Only use filename part
    setup_logging(log_file=log_file, log_format=f'%(asctime)s - %(levelname)s - {matrix_id} - %(message)s')
        
    # Run the scraper
    if args.site == 'KY':
        scraper = KitapYurduScraper(matrix_id, args.workers)
    elif args.site == 'BKM':
        scraper = BkmKitapScraper(matrix_id, args.workers)
    else:
        print(f"Unknown site: {args.site}")
        sys.exit(1)
        
    try:
        logging.info(f"Starting {args.site} scraper with matrix_id {matrix_id}")
        scraper.run()
        logging.info(f"{args.site} scraping completed successfully")
        print(f"{args.site} scraping completed successfully")
    except Exception as e:
        logging.error(f"Error running {args.site} scraper: {e}", exc_info=True)
        print(f"ERROR: {args.site} scraping failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
