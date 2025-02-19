import pandas as pd
import numpy as np
import os
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
import requests

import logging

from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_fixed

from additional import log_config

headers = {
    'User-Agent': 'Chrome/91.0.4472.124',
    'Accept': 'text/html'
}
#Parametreler
format = "%Y-%m-%d %H:%M:%S"
matrix=os.getenv('matrix_id')
filename = "Dataset/KY_"+matrix+".csv"
workers_count=int(os.getenv('WORKERS_COUNT'))

log_config(os.getenv('CLUSTER_LOG_FILE'),f'%(asctime)s - %(levelname)s - {matrix} - %(message)s')

# JSON dosyasını oku ve Kategorileri links değerine yaz
links=[]
categories_file = os.getenv('categories_file')
logging.debug("Reading categories file: %s", categories_file)

with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    categori_id=categori["categori_id"]
    links.append(f"https://www.kitapyurdu.com/index.php?filter_category_all=true&filter_in_stock=1&sort=purchased_365&order=DESC&route=product/category&limit=100&category_id={categori_id}")
    

column=["Kitap İsmi","Yazar","Yayın Evi","ISBN","Dil","Sayfa","Kategori","Fiyat","URL","Platform","Tarih","Kapak Resmi","Reiting","Reiting Count","NLP-Data"]

#Dataset Dosyasını Oku
data = pd.read_csv("Data/KY_Datasets.csv", sep=";")
column=data.columns
# Yeni veri oluşturma
df = pd.DataFrame(columns=column)
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

def get_sayfa_sayisi(soup):
    try:
        # Sayfa numaralarını bulma
        pagination_div = soup.find("div", class_="pagination")
        if pagination_div:
            results_div = pagination_div.find("div", class_="results")
            if results_div:
                match = re.search(r'\((\d+) Sayfa\)', results_div.text)
                if match:
                    return int(match.group(1))
                else:
                    return 1
            else:
                return 1
        else:
            return 1
    except:
        logging.error("Failed to extract page count from BS4 Data")

def get_data(soup):
    listeData = []
    try:
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
            except Exception as e:
                publisher = ""
                author = ""
                rating = ""
                rating_count = ""
                NLP_Data = ""
                logging.debug("Failed to extract some details for %s - %s: %s", title,url, str(e))
            converted_price = tur_degistir(price)
            last_price = float(son_fiyat_sorgu(url))
            if converted_price != last_price:
                listeData.append([title, author, publisher, "", "", "", category, converted_price, url, "Kitap Yurdu", datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format), img, rating, rating_count, NLP_Data])
    except Exception as e:
        logging.debug("Failed to read data in get_Data: %s", str(e))

    return listeData


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def process_page(url):
    response = requests.get(url,headers=headers,verify=False,timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    data = get_data(soup)
    return data

def veri_al(link):
    CurrentDF=pd.DataFrame(columns = column)
    url = link
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    sayfasayi=get_sayfa_sayisi(soup)
    logging.info(f"Page Count: {sayfasayi}")

    urls = [f"{link}&page={i}" for i in range(1, sayfasayi + 1)]
    
    with ThreadPoolExecutor(max_workers=workers_count) as executor:
        results = list(executor.map(process_page, urls))
    
    for result in results:
        CurrentDF = pd.concat([CurrentDF, pd.DataFrame(result, columns=column)], ignore_index=True)

    return CurrentDF

logging.info("Starting data scraping")
for link in links:
    logging.info("Scraping data for category: %s", link)
    df = pd.concat([df,pd.DataFrame(veri_al(link),columns = column)])
    
df.reset_index(inplace=True)
df.drop("index",axis=1,inplace=True)
df.to_csv(filename,sep=';',index=False,encoding="utf-8")

logging.info("Data scraping completed")
logging.shutdown()