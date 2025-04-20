import logging
import pandas as pd
from datetime import datetime
from pytz import timezone
import requests
from bs4 import BeautifulSoup
import sys
import os

# Modül import yolunu düzeltiyoruz
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts.scrapers.base_scraper import BaseScraper


class BkmKitapScraper(BaseScraper):
    """Scraper for BKM Kitap website"""
    
    def __init__(self, matrix_id=None, workers_count=5):
        super().__init__("BKM", matrix_id, workers_count)
        self.site_url = "https://www.bkmkitap.com"
        self.setup_logging()
        
    def scrape_categories(self):
        """Scrape categories from BKM Kitap website"""
        links = []
        logging.info(f"Starting to scrape categories from {self.site_url}")
        
        url = f"{self.site_url}/kategori-listesi"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            logging.info(f"Successfully fetched the category list from {url}")
        except requests.RequestException as e:
            logging.error(f"Error fetching the category list: {str(e)}")
            return links
            
        soup = BeautifulSoup(response.content, "html.parser")
        categories = soup.find_all("a", class_=["w-100 d-block block-title"])
        
        for category in categories:
            try:
                name = str(category.text)
                url = str(self.site_url + category['href'] + '?&stock=1')
                
                link = {
                    'name': name,
                    'url': url
                }
                links.append(link)
                logging.debug(f"Found category: {name}")
            except Exception as e:
                logging.error(f"Error parsing category: {str(e)}")
                
        return links
    
    def get_pagination(self, soup):
        """Get total number of pages from pagination"""
        try:
            pagination = soup.find("div", class_="pagination")
            page_numbers = []
            
            if pagination:
                for a in pagination.find_all("a"):
                    if 'pg=' in a['href']:
                        page_number = int(a['href'].split('pg=')[-1])
                        page_numbers.append(page_number)
            
            if page_numbers:
                return max(page_numbers)
            return 1
        except Exception as e:
            logging.error(f"Failed to extract page count: {e}")
            return 1
            
    def generate_pagination_urls(self, base_url, page_count):
        """Generate URLs for all pages in a category"""
        urls = []
        for i in range(1, page_count + 1):
            # BKM uses pg parameter for pagination
            if '?' in base_url:
                urls.append(f"{base_url}&pg={i}")
            else:
                urls.append(f"{base_url}?pg={i}")
        return urls
        
    def process_page(self, url):
        """Process a single page"""
        soup = self.fetch_page(url)
        return self.scrape_products(soup)
        
    def scrape_products(self, soup):
        """Extract product data from a page"""
        product_list = []
        
        try:
            # Get category name
            category = ""
            try:
                category = soup.find("input", {"id": "category-name"}).get("value")
            except:
                category_breadcrumb = soup.find("div", class_="breadcrumb")
                if category_breadcrumb:
                    last_link = category_breadcrumb.find_all("a")[-1]
                    category = last_link.text.strip()
            
            product_items = soup.find_all("div", class_="product-item")
            logging.info(f"Found {len(product_items)} products")
            
            for item in product_items:
                try:
                    # Extract basic info
                    title = item.find("a", class_="product-title").text.strip()
                    author = item.find("a", class_="model-title").text.strip()
                    publisher = item.find("a", class_="brand-title").text.strip()
                    price_str = item.find("span", class_="product-price").text.strip()
                    img = item.find('img')['data-src']
                    url = f"{self.site_url}{item.find('a', class_='product-title')['href']}"
                    
                    # BKM has bigger image urls
                    img_big = img.replace('-K.jpg', '-O.jpg')
                    
                    # Convert and compare price
                    current_price = self.convert_price(price_str)
                    last_price = self.get_last_price(url)
                    
                    if current_price != last_price:
                        # Standardize column order based on self.site_columns
                        product_data = [
                            title,              # Kitap İsmi
                            author,             # Yazar
                            publisher,          # Yayınevi
                            category,           # Kategori
                            current_price,      # Fiyat
                            url,                # URL
                            "BKM Kitap",        # Site
                            datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(self.datetime_format), # Tarih
                            img,                # Resim
                            img_big             # ResimBüyük
                        ]
                        product_list.append(product_data)
                
                except Exception as e:
                    logging.debug(f"Error processing product: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error scraping products: {str(e)}")
            
        return product_list


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    scraper = BkmKitapScraper()
    scraper.run()