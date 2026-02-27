import logging
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from pytz import timezone
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed
import requests
from bs4 import BeautifulSoup
import sys

# Modül import yolunu düzenleme
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class BaseScraper(ABC):
    """Base class for all web scrapers in the project"""
    
    def __init__(self, site_name, matrix_id=None, workers_count=5):
        self.site_name = site_name
        self.matrix_id = matrix_id or os.getenv('matrix_id')
        self.workers_count = int(os.getenv('WORKERS_COUNT', workers_count))
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.categories_file = os.getenv('categories_file')
        self.dataset_path = f"Data/{self.site_name}_Datasets.csv"
        self.output_path = f"Dataset/{self.site_name}_{self.matrix_id}.csv"
        self.headers = {
            'User-Agent': 'Chrome/91.0.4472.124',
            'Accept': 'text/html'
        }
        
        # Standardize columns for both sites
        # These are the common columns for both KY and BKM
        self.standard_columns = [
            "Kitap İsmi", "Yazar", "Yayınevi", "Kategori", "Fiyat", 
            "URL", "Site", "Tarih", "Resim"
        ]
        
        # Specific columns based on site
        if self.site_name == "KY":
            self.site_columns = self.standard_columns + ["Puan", "Değerlendirme Sayısı", "NLP Data"]
        else:  # BKM
            self.site_columns = self.standard_columns + ["ResimBüyük"]
        
        # Existing data for price comparison
        self.data_df = None
        self.price_compare_df = None
        
    def setup_logging(self, log_file=None, log_format=None):
        """Configure logging for the scraper"""
        if not log_file:
            log_file = os.getenv('CLUSTER_LOG_FILE', f"{self.site_name}.log")
        
        if not log_format:
            log_format = f'%(asctime)s - %(levelname)s - {self.matrix_id} - %(message)s'
            
        from Scripts.logging_utils import setup_logging
        setup_logging(log_file=log_file, log_format=log_format)
        
    def load_dataset(self):
        """Load existing dataset for comparison"""
        try:
            self.data_df = pd.read_csv(self.dataset_path, sep=";")
            logging.info(f"Loaded existing dataset with {len(self.data_df)} records")
            
            # Prepare price comparison dataframe
            if 'URL' in self.data_df.columns and 'Tarih' in self.data_df.columns and 'Fiyat' in self.data_df.columns:
                self.price_compare_df = self.data_df.groupby(['URL']).agg(Tarih=('Tarih', np.max))
                self.price_compare_df = pd.merge(
                    self.price_compare_df, 
                    self.data_df[['URL', 'Tarih', 'Fiyat']], 
                    how='left', 
                    on=['URL', 'Tarih']
                )
                logging.info("Price comparison dataframe prepared")
            else:
                logging.warning("Required columns not found in dataset. Price comparison disabled.")
                self.price_compare_df = pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading dataset: {e}")
            self.data_df = pd.DataFrame(columns=self.site_columns)
            self.price_compare_df = pd.DataFrame()
            
    def load_categories(self):
        """Load categories from JSON file"""
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                categories = json.load(f)
            logging.info(f"Loaded {len(categories)} categories from {self.categories_file}")
            return categories
        except Exception as e:
            logging.error(f"Error loading categories: {e}")
            return []
            
    def get_last_price(self, url):
        """Get the last price for a URL"""
        if self.price_compare_df is None:
            self.load_dataset()
            
        try:
            if self.price_compare_df.empty:
                return 0.0
                
            # Değişken ismi değil, dataframe sütun ismi olarak 'URL' kullanıyoruz
            result = self.price_compare_df[self.price_compare_df["URL"] == url]["Fiyat"]
            if len(result) > 0:
                return float(result.iloc[0])
            else:
                return 0.0
        except Exception as e:
            logging.warning(f"Error getting last price for URL {url}: {e}")
            return 0.0
    
    def convert_price(self, price_str):
        """Convert price string to float"""
        try:
            x = price_str.rsplit(',', 1)
            x[0] = x[0].replace(".", "")
            x = x[0] + "." + x[1]
            return float(x)
        except Exception as e:
            logging.warning(f"Error converting price {price_str}: {e}")
            return 0.0
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch_page(self, url):
        """Fetch a page with retry logic"""
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            logging.error(f"Error fetching page {url}: {e}")
            raise
            
    def scrape_with_threading(self, urls, process_function):
        """Scrape multiple pages using threading"""
        results = []
        with ThreadPoolExecutor(max_workers=self.workers_count) as executor:
            results = list(executor.map(process_function, urls))
        return results
        
    def save_dataframe(self, df):
        """Save dataframe to CSV"""
        try:
            if df.empty:
                logging.warning("No data to save")
                return
            
            df.reset_index(inplace=True, drop=True)
            if "index" in df.columns:
                df.drop("index", axis=1, inplace=True)
            df.to_csv(self.output_path, sep=';', index=False, encoding="utf-8")
            logging.info(f"Saved {len(df)} records to {self.output_path}")
        except Exception as e:
            logging.error(f"Error saving dataframe: {e}")
            
    @abstractmethod
    def scrape_categories(self):
        """Scrape categories from the website"""
        pass
        
    @abstractmethod
    def scrape_products(self, url):
        """Scrape products from a category URL"""
        pass
        
    @abstractmethod
    def get_pagination(self, soup):
        """Get pagination info from a page"""
        pass
        
    def run(self):
        """Run the scraper"""
        logging.info(f"Starting {self.site_name} scraper with matrix_id {self.matrix_id}")
        self.load_dataset()
        categories = self.load_categories()
        
        # Create result DataFrame with correct columns
        result_df = pd.DataFrame(columns=self.site_columns)
        
        for category in categories:
            try:
                category_url = self.get_category_url(category)
                logging.info(f"Processing category: {category_url}")
                category_data = self.scrape_category(category_url, category)
                if not category_data.empty:
                    result_df = pd.concat([result_df, category_data], ignore_index=True)
            except Exception as e:
                logging.error(f"Error processing category {category}: {e}")
                
        self.save_dataframe(result_df)
        logging.info("Scraping completed")
        
    def get_category_url(self, category):
        """Get the URL for a category"""
        if isinstance(category, dict) and 'url' in category:
            return category['url']
        return category
        
    def scrape_category(self, url, category_info):
        """Scrape a category"""
        soup = self.fetch_page(url)
        page_count = self.get_pagination(soup)
        logging.info(f"Found {page_count} pages for category")
        
        urls = self.generate_pagination_urls(url, page_count)
        results = self.scrape_with_threading(urls, self.process_page)
        
        # Prepare an empty DataFrame with the correct columns
        all_products = []
        
        # Process and combine all results
        for page_data in results:
            if page_data:
                all_products.extend(page_data)
                
        # Create DataFrame only if there are products
        if all_products:
            category_df = pd.DataFrame(all_products, columns=self.site_columns)
            return category_df
        else:
            return pd.DataFrame(columns=self.site_columns)
    
    @abstractmethod
    def generate_pagination_urls(self, base_url, page_count):
        """Generate URLs for all pages in a category"""
        pass
        
    @abstractmethod
    def process_page(self, url):
        """Process a single page"""
        pass
