import re
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


class KitapYurduScraper(BaseScraper):
    """Scraper for Kitap Yurdu website"""
    
    def __init__(self, matrix_id=None, workers_count=5):
        super().__init__("KY", matrix_id, workers_count)
        self.site_url = "https://www.kitapyurdu.com"
        self.setup_logging()
        
    def scrape_categories(self):
        """Scrape categories from Kitap Yurdu website"""
        links = []
        logging.info(f"Starting to scrape categories from {self.site_url}")
        
        url = f"{self.site_url}/index.php?route=product/category"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                logging.info(f"Successfully fetched the category list from {url}")
            else:
                logging.error(f"Failed to fetch the category list from {url} - Response Status: {response.status_code}")
                return links
        except requests.RequestException as e:
            logging.error(f"Error fetching the category list: {str(e)}")
            return links
            
        soup = BeautifulSoup(response.content, "html.parser")
        categories = soup.find_all("div", class_="category")
        
        for category in categories:
            try:
                name = str(category.find("h2").text)
                url = str(category.find("a", class_="category-item")["href"])
                category_id = re.search(r'/(\d+)\.html$', url).group(1)
                
                link = {
                    'name': name,
                    'url': url,
                    'categori_id': category_id
                }
                links.append(link)
                logging.info(f"Found category: {name} ({category_id})")
            except Exception as e:
                logging.error(f"Error parsing category: {str(e)}")
                
        return links
        
    def get_category_url(self, category):
        """Get formatted category URL with filters"""
        category_id = category.get('categori_id')
        return f"{self.site_url}/index.php?filter_category_all=true&filter_in_stock=1&sort=purchased_365&order=DESC&route=product/category&limit=100&category_id={category_id}"
    
    def get_pagination(self, soup):
        """Get total number of pages from pagination"""
        try:
            pagination_div = soup.find("div", class_="pagination")
            if pagination_div:
                results_div = pagination_div.find("div", class_="results")
                if results_div:
                    match = re.search(r'\((\d+) Sayfa\)', results_div.text)
                    if match:
                        return int(match.group(1))
            return 1
        except Exception as e:
            logging.error(f"Failed to extract page count: {e}")
            return 1
            
    def generate_pagination_urls(self, base_url, page_count):
        """Generate URLs for all pages in a category"""
        return [f"{base_url}&page={i}" for i in range(1, page_count + 1)]
        
    def process_page(self, url):
        """Process a single page"""
        soup = self.fetch_page(url)
        return self.scrape_products(soup)
        
    def scrape_products(self, soup):
        """Extract product data from a page"""
        product_list = []
        
        try:
            category = soup.find("div", id="content").find("h1").text.strip()
            products = soup.find_all("div", class_="product-cr")
            logging.info(f"Found {len(products)} products")
            
            for product in products:
                try:
                    # Extract basic info
                    img = product.find("div", class_="cover").find("a").find("img")["src"].replace("/wi:100/wh:true", "")
                    title = product.find("div", class_="name").find("a")["title"].strip()
                    url = product.find("a", class_="pr-img-link").get("href")
                    url = re.match(r"(.*?\.html).*", url).group(1)
                    price_str = product.find("div", class_="price").find("span", class_="value").text.strip()
                    
                    # Extract additional details
                    try:
                        publisher = product.find("div", class_="publisher").text.strip()
                        author = product.find("div", class_="author compact ellipsis").text.strip()
                        rating_div = product.find("div", class_="rating").find("div")
                        rating = rating_div["title"].strip().split(" ")[0] if rating_div else ""
                        rating_count = len(product.select(".rating .fa.fa-star.active"))
                        nlp_data = product.find("div", class_="product-info").text.strip()
                    except Exception as e:
                        publisher = ""
                        author = ""
                        rating = ""
                        rating_count = ""
                        nlp_data = ""
                        logging.debug(f"Failed to extract some details for {title} - {url}: {str(e)}")
                    
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
                            "Kitap Yurdu",      # Site
                            datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(self.datetime_format), # Tarih
                            img,                # Resim
                            rating,             # Puan
                            rating_count,       # Değerlendirme Sayısı
                            nlp_data            # NLP Data
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
    
    scraper = KitapYurduScraper()
    scraper.run()