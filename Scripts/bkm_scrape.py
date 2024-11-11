import os
import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pytz import timezone

from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed

import logging
from additional import log_config

#Parametreler
format = "%Y-%m-%d %H:%M:%S"
matrix= os.getenv('matrix_id')
filename = "Dataset/BKM_"+matrix+".csv"
workers_count=int(os.getenv('WORKERS_COUNT'))

log_config(os.getenv('CLUSTER_LOG_FILE'),f'%(asctime)s - %(levelname)s - {matrix} - %(message)s')

# JSON dosyasını oku ve Kategorileri links değerine yaz
links=[]
categories_file = os.getenv('categories_file')
logging.info("Reading categories file: %s", categories_file)

with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    links.append(categori["url"])

columns=["Kitap İsmi", "Yazar", "Yayın Evi", "Fiyat",
                  "URL", "Platform", "Tarih", "Kapak Kucultulmus", "Kapak Resmi","Category"]

#Dataset Dosyasını Oku
data = pd.read_csv("Data/BKM_Datasets.csv", sep=";")
column=data.columns
# Yeni veri oluşturma
dataset = pd.DataFrame(columns=column)

grup = data.groupby(['URL']).agg(Tarih=('Tarih', np.max))

grup=pd.merge(grup,data[['URL','Tarih','Fiyat']],how='left', on=['URL','Tarih'])

def tur_degistir(fiyat):
    x=fiyat.rsplit(',',1)
    x[0]=x[0].replace(".", "")
    x=x[0]+"."+x[1]
    converted_price = float(x)
    return converted_price

def son_fiyat_sorgu(link):
    URL_filter_data = grup.query("URL ==@link")["Fiyat"]
    if URL_filter_data.count()!=0:
        URL_filter_data = float(URL_filter_data.iloc[0])
    else:
        URL_filter_data=0.0
        logging.warning("No price data found for link %s. Defaulting to %f", link, URL_filter_data)
    return URL_filter_data
    
def get_data(soup):
    listeData=[]
    try:
        category=soup.find("input", {"id": "category-name"}).get("value")
        product_items = soup.find_all("div", class_="product-item")
        logging.info("Found %d products", len(product_items))
        for item in product_items:
            title= item.find("a", class_="product-title").text.strip()
            author = item.find("a", class_="model-title").text.strip()
            publisher = item.find("a", class_="brand-title").text.strip()
            price = item.find("span", class_="product-price").text.strip()
            img = item.find('img')['data-src']
            url = f"https://www.bkmkitap.com{item.find('a', class_='product-title')['href']}"
            converted_price = tur_degistir(price)
            last_price = float(son_fiyat_sorgu(url))
            if converted_price != last_price:
                listeData.append([title, author, publisher, tur_degistir(price), url, "BKM Kitap",datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format), img,img.replace('-K.jpg', '-O.jpg'),category])
    except Exception as e:
        logging.error("Failed to read data in get_data: %s", str(e))
    return listeData


    
def get_sayfa_sayisi(soup):
    try:
        # Sayfa numaralarını bulma
        pagination = soup.find("div", class_="pagination")
        page_numbers = []
        if pagination:
            for a in pagination.find_all("a"):
                if 'pg=' in a['href']:
                    page_number = int(a['href'].split('pg=')[-1])
                    page_numbers.append(page_number)
        # En yüksek sayfa numarasını alma
        if page_numbers:
            return max(page_numbers)
        else:
            return 1
    except:
        logging.error("Failed to extract page count from BS4 Data")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def process_page(url):
    response = requests.get(url,verify=False,timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    data = get_data(soup)
    return data

def veri_al(link):
    CurrentDF=pd.DataFrame(columns = column)
    url = link
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    sayfasayi=get_sayfa_sayisi(soup)
    logging.info(f"Page Count: {sayfasayi}")

    urls = [f"{link}?pg={i}" for i in range(1, sayfasayi + 1)]
    
    with ThreadPoolExecutor(max_workers=workers_count) as executor:
        results = list(executor.map(process_page, urls))
    
    for result in results:
        CurrentDF = pd.concat([CurrentDF, pd.DataFrame(result, columns=columns)], ignore_index=True)

    return CurrentDF

# LOG yapısı oluştur
logging.debug("Starting data scraping")

for link in links:
    logging.debug("Scraping data for category: %s", link)
    print("Kategori : "+link)
    dataset = pd.concat([dataset,pd.DataFrame(veri_al(link),columns = column)])

dataset.reset_index(inplace=True)
dataset.drop("index",axis=1,inplace=True)
dataset.to_csv(filename,sep=';',index=False,encoding="utf-8")
logging.debug("Data scraping %s completed", filename)

logging.info("Data scraping completed")
logging.shutdown()