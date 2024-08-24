import os
import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pytz import timezone

import logging
from additional import log_config

#Parametreler
format = "%Y-%m-%d %H:%M:%S"
matrix= os.getenv('matrix_id')
filename = "Dataset/BKM_"+matrix+".csv"

log_config(os.getenv('CLUSTER_LOG_FILE'),f'%(asctime)s - %(name)s - %(levelname)s - {matrix} - %(message)s')

# JSON dosyasını oku ve Kategorileri links değerine yaz
links=[]
categories_file = os.getenv('categories_file')
logging.info("Reading categories file: %s", categories_file)

with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    links.append(categori["url"])

columns=["Kitap İsmi", "Yazar", "Yayın Evi", "Fiyat",
                  "URL", "Platform", "Tarih", "Kapak Kucultulmus", "Kapak Resmi"]

#Dataset Dosyasını Oku
logging.info("Reading dataset file: Data/BKM_Datasets.csv")
data = pd.read_csv("Data/BKM_Datasets.csv", sep=";")
column=data.columns
logging.info("Columns in dataset: %s", str(column))
# Yeni veri oluşturma
dataset = pd.DataFrame(columns=column)
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
    
def get_data(soup):
    listeData=[]
    try:
        logging.info("Extracting category and products from soup")
        category=soup.find_all('span', property='name')[-1].text
        urunler = soup.find_all("div", class_="productItem")
        logging.info("Found %d products", len(urunler))
        for urun in urunler:
            title= urun.find("a", class_="fl col-12 text-description detailLink").text.strip()
            author = urun.find("a", class_="fl col-12 text-title").text.strip()
            publisher = urun.find("a", class_="col col-12 text-title mt").text.strip()
            price = urun.find("div", class_="col col-12 currentPrice").text.strip().replace("\nTL", "").strip()
            img = urun.find("img", class_="lazy stImage")["data-src"]
            url = f"https://www.bkmkitap.com{urun.find('a', class_='fl col-12 text-description detailLink')['href']}"
            logging.info("Processing product: %s", title)
            converted_price = tur_degistir(price)
            last_price = float(son_fiyat_sorgu(url))
            if converted_price != last_price:
                logging.info("Price change detected for %s: %f -> %f", title, last_price, converted_price)
                listeData.append([title, author, publisher, tur_degistir(price), url, "BKM Kitap",datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format), img,img.replace('-K.jpg', '-O.jpg')])
    except Exception as e:
        logging.error("Failed to read data in get_data: %s", str(e))
    return listeData


    
def get_sayfa_sayisi(soup):
    try:
        logging.info("Extracting page count from BS4 Data")
        sayi=[]
        sayfasayi = soup.find_all("div", {"class": "fr col-sm-12 text-center productPager"})
        sayfasayi = str(sayfasayi)
        words = re.findall(r'>\S+</a>', sayfasayi)
        for w in words:
            w = w.replace('>', '')
            w = w.replace('</a', '')
            w = w.split(",")
            if w != "...":
                sayi.append(w[0])
        page_count = int(sayi[-1])
        logging.info("Page count: %d", page_count)
        return page_count
    except:
        logging.error("Failed to extract page count from BS4 Data")
        return int(1)
    

def veri_al(link):
    CurrentDF=pd.DataFrame(columns = column)
    url = link
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    sayfasayi=get_sayfa_sayisi(soup)
    print("Sayfa Sayisi : "+str(sayfasayi))
    i=1
    while i<= int(sayfasayi):
        url = link+"?pg="+str(i)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        CurrentDF = pd.concat([CurrentDF,pd.DataFrame(get_data(soup),columns = column)])
        i=i+1
    return CurrentDF

# LOG yapısı oluştur
logging.info("Starting data scraping")

for link in links:
    logging.info("Scraping data for category: %s", link)
    print("Kategori : "+link)
    dataset = pd.concat([dataset,pd.DataFrame(veri_al(link),columns = column)])

dataset.reset_index(inplace=True)
dataset.drop("index",axis=1,inplace=True)
dataset.to_csv(filename,sep=';',index=False,encoding="utf-8")
logging.info("Data scraping %s completed", filename)

logging.info("Data scraping completed")
logging.shutdown()