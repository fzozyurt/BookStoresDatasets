import pandas as pd
import numpy as np
import os
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone

from Selenium import initialize_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import logging
from additional import log_config

#Parametreler
format = "%Y-%m-%d %H:%M:%S"
matrix=os.getenv('matrix_id')
filename = "Dataset/KY_"+matrix+".csv"
log_config(os.getenv('CLUSTER_LOG_FILE'),f'%(asctime)s - %(levelname)s - {matrix} - %(message)s')

# JSON dosyasını oku ve Kategorileri links değerine yaz
links=[]
categories_file = os.getenv('categories_file')
logging.info("Reading categories file: %s", categories_file)

with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    links.append(categori["url"])

column=["Kitap İsmi","Yazar","Yayın Evi","ISBN","Dil","Sayfa","Kategori","Fiyat","URL","Platform","Tarih","Kapak Resmi","Reiting","Reiting Count","NLP-Data"]

#Dataset Dosyasını Oku
data = pd.read_csv("Data/KY_Datasets.csv", sep=";")
column=data.columns
logging.info("Columns in dataset: %s", str(column))
# Yeni veri oluşturma
df = pd.DataFrame(columns=column)
logging.info("Empty dataset created with columns: %s", str(column))

logging.info("Grouping data by 'URL' and aggregating 'Tarih'")
grup = data.groupby(['URL']).agg(Tarih=('Tarih', np.max))
logging.info("Data grouped successfully")

logging.info("Merging grouped data with original data on 'URL' and 'Tarih'")
grup=pd.merge(grup,data[['URL','Tarih','Fiyat']],how='left', on=['URL','Tarih'])
logging.info("Data merged successfully with %d rows", grup.shape[0])

def tur_degistir(fiyat):
    logging.info("Original price string: %s", fiyat)
    x=fiyat.rsplit(',',1)
    x[0]=x[0].replace(".", "")
    x=x[0]+"."+x[1]
    converted_price = float(x)
    logging.info("Converted Price: %s", converted_price)
    return converted_price

def son_fiyat_sorgu(link):
    logging.info("Querying last price for link: %s", link)
    URL_filter_data = grup.query("URL ==@link")["Fiyat"]
    if URL_filter_data.count()!=0:
        URL_filter_data = float(URL_filter_data.iloc[0])
    else:
        URL_filter_data=0.0
        logging.warning("No price data found for link %s. Defaulting to %f", link, URL_filter_data)
    logging.info("Last price for link %s: %f", link, URL_filter_data)
    return URL_filter_data

def get_Data(soup):
    listeData = []
    try:
        logging.info("Extracting category and products from soup")
        category = soup.find("div", id="content").find("h1").text.strip()
        products = soup.find_all("div", class_="product-cr")
        logging.info("Found %d products", len(products))
        
        for product in products:
            img = product.find("div", class_="cover").find("a").find("img")["src"].replace("/wi:100/wh:true", "")
            title = product.find("div", class_="name").find("a")["title"].strip()
            url = product.find("a", class_="pr-img-link").get("href")
            url = re.match(r"(.*?\.html).*", url).group(1)
            price = product.find("div", class_="price").find("span", class_="value").text.strip()
            
            try:
                publisher = product.find("div", class_="publisher").text.strip()
                author = product.find("div", class_="author compact ellipsis").text.strip()
                rating = product.find("div", class_="rating").find("div")["title"].strip().split(" ")[0]
                rating_count = len(product.select(".rating .fa.fa-star.active"))
                NLP_Data = product.find("div", class_="product-info").text.strip()
                logging.info("Processed product details for %s", title)
            except Exception as e:
                publisher = ""
                author = ""
                rating = ""
                rating_count = ""
                NLP_Data = ""
                logging.warning("Failed to extract some details for %s: %s", title, str(e))
            converted_price = tur_degistir(price)
            last_price = float(son_fiyat_sorgu(url))
            if converted_price != last_price:
                logging.info("Price change detected for %s: %f -> %f", title, last_price, converted_price)
                listeData.append([title, author, publisher, "", "", "", category, converted_price, url, "Kitap Yurdu", datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format), img, rating, rating_count, NLP_Data])
            else:
                logging.info("No price change for %s", title)
    except Exception as e:
        logging.error("Failed to read data in get_Data: %s", str(e))
    
    return listeData

def veri_al(link):
    url = link
    logging.info("Navigating to URL: %s", url)
    wd.get(url)
    try:
        wd.find_element(By.XPATH, "//*[@id='list_product_carousel_best_sell-view-all']").click()
        logging.info("Clicked on 'view all' for best selling products")
    except Exception as e:
        logging.warning("Kategori Seçim Atlandı: %s", str(e))
    
    logging.info("Current URL: %s", wd.current_url)
    try:
        drop = wd.find_element(By.XPATH, "//*[@id='content']/div/div[1]/div/div[2]/select")  # 100 Öğre Gösterme Seçimi
        drop = Select(drop)
        drop.select_by_visible_text("100 Ürün")
        logging.info("Selected '100 Ürün' from dropdown")
    except Exception as e:
        logging.error("Failed to select '100 Ürün' from dropdown: %s", str(e))
    
    logging.info("Current URL after dropdown selection: %s", wd.current_url)
    if WebDriverWait(wd, 30).until(EC.url_changes(url=url)):
        try:
            sayfasayisi = wd.find_element(By.XPATH, "//*[@id='content']/div/div[3]/div[2]").text.split(" ")[7].replace("(", "")  # Sayfa Sayısı Kısmının TEXT ini alıyoruz
            logging.info("Number of pages: %s", sayfasayisi)
        except Exception as e:
            logging.warning("Failed to get number of pages, defaulting to 1: %s", str(e))
            sayfasayisi = 1
        
        i = 1
        CurrentDF = pd.DataFrame(columns=column)
        while i <= int(sayfasayisi):
            try:
                products_container = wd.find_element(By.CSS_SELECTOR, "#content ")
                soup = BeautifulSoup(products_container.get_attribute("outerHTML"), "html.parser")
                CurrentDF = pd.concat([CurrentDF, pd.DataFrame(get_Data(soup), columns=column)])
                logging.info("Extracted data from page %d", i)
                
                try:
                    cur_url = wd.current_url
                    wd.find_element(By.CSS_SELECTOR, "a.next").click()
                    if WebDriverWait(wd, 30).until(EC.url_changes(url=cur_url)):
                        i += 1
                        logging.info("Navigated to next page: %d", i)
                except Exception as e:
                    try:
                        if WebDriverWait(wd, 5).until(EC.visibility_of_element_located((By.ID, "cookiescript_accept"))):
                            wd.find_element(By.ID, "cookiescript_accept").click()
                            cur_url = wd.current_url
                            wd.find_element(By.CSS_SELECTOR, "a.next").click()
                            if WebDriverWait(wd, 30).until(EC.url_changes(url=cur_url)):
                                i += 1
                                logging.info("Accepted cookies and navigated to next page: %d", i)
                    except Exception as e:
                        logging.error("Failed to navigate to next page after accepting cookies: %s", str(e))
                        break
            except Exception as e:
                logging.error("Failed to process page %d: %s", i, str(e))
                break
    return CurrentDF

logging.info("Starting data scraping")
wd= initialize_driver()
for link in links:
    logging.info("Scraping data for category: %s", link)
    df = pd.concat([df,pd.DataFrame(veri_al(link),columns = column)])
    
df.reset_index(inplace=True)
df.drop("index",axis=1,inplace=True)
df.to_csv(filename,sep=';',index=False,encoding="utf-8")
logging.info("Data scraping %s completed", filename)

logging.info("Data scraping completed")
logging.shutdown()