import pandas as pd
import numpy as np
import os
import sys
import time
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone

import logging

from Selenium import initialize_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(filename="selenium.log", level=logging.INFO)

#Parametreler
format = "%Y-%m-%d %H:%M:%S"
matrix=os.getenv('matrix_id')
filename = "Dataset/KY_"+matrix+".csv"

# JSON dosyasını oku ve Kategorileri links değerine yaz
links=[]
categories_file = os.getenv('categories_file')

with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    links.append(categori["url"])

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
    return float(x)

def son_fiyat_sorgu(link):
    URL_filter_data = grup.query("URL ==@link")["Fiyat"]
    if URL_filter_data.count()!=0:
        return float(URL_filter_data)
    else:
        URL_filter_data=0.0
        return URL_filter_data

def Get_Data(soup):
    listeData=[]
    category=soup.find("div", id="content").find("h1").text.strip()
    for product in soup.find_all("div", class_="product-cr"):
        img=product.find("div", class_="cover").find("a").find("img")["src"].replace("/wi:100/wh:true","")
        title = product.find("div", class_="name").find("a")["title"].strip()
        url = product.find("a", class_="pr-img-link").get("href")
        url=re.match(r"(.*?\.html).*", url).group(1)
        price=product.find("div", class_="price").find("span",class_="value").text.strip()
        try:
            publisher = product.find("div", class_="publisher").text.strip()
            author = product.find("div", class_="author compact ellipsis").text.strip()
            raiting=product.find("div", class_="rating").find("div")["title"].strip().split(" ")[0]
            raiting_count= len(product.select(".rating .fa.fa-star.active"))
            NLP_Data=product.find("div", class_="product-info").text.strip()
            #if NLP_Data:
                #eslesme = re.search("[0-9]{13}", NLP_Data)
                #if eslesme: ISBN=eslesme.group()
        except:
            publisher = ""
            author = ""
            raiting=""
            raiting_count= ""
            NLP_Data=""
            #ISBN=""
            print("Detay Atlandı")
        if tur_degistir(price)!=float(son_fiyat_sorgu(url)):
            listeData.append([title,author,publisher,"","","",category,tur_degistir(price),url,"Kitap Yurdu",datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format),img,raiting,raiting_count,NLP_Data])
        else:
            logging.info("{} {} Fiyat değişmediğinden ekleme yapılmadı.",url)
    return listeData

def veri_al(link):
    url=link
    wd.get(url)
    logging.info("Sayfa açıldı: {}".format(wd.current_url))
    try:
        wd.find_element(By.XPATH,"//*[@id='list_product_carousel_best_sell-view-all']").click()
    except:
         logging.info("Tek Kategori. Tümünü listele atlandı. URL: {}".format(wd.current_url))
    print(wd.current_url)
    drop=wd.find_element(By.XPATH,"//*[@id='content']/div/div[1]/div/div[2]/select") #100 Öğre Gösterme Seçimi
    drop = Select(drop)
    drop.select_by_visible_text("100 Ürün")
    logging.info("100 öğe listele seçildi")
    print(wd.current_url)
    if WebDriverWait(wd, 30).until(EC.url_changes(url=url)):
        #wd.find_element(By.XPATH,"//*[@id='content']/div/div[1]/div/div[3]/a").click() # Yatay görünüme Geç
       #logging.info("Yatay görünüme geçildi")
        try:
            sayfasayisi=wd.find_element(By.XPATH,"//*[@id='content']/div/div[3]/div[2]").text.split(" ")[7].replace("(","") #Sayfa Sayısı Kısmının TEXT ini alıyoruz
        except:
            sayfasayisi=1
        i=1
        CurrentDF=pd.DataFrame(columns = column)
        while i<= int(sayfasayisi):
            logging.info("{} sayfa scrapping başlatıldı.",i)
            logging.info("Sayfa URL: {}".format(wd.current_url))
            products_container = wd.find_element(By.CSS_SELECTOR, "#content ")
            soup = BeautifulSoup(products_container.get_attribute("outerHTML"), "html.parser")
            #print(soup.find("div", class_="name").text.strip())
            CurrentDF = pd.concat([CurrentDF,pd.DataFrame(Get_Data(soup),columns = column)])
            try:
                try:
                    cur_url=wd.current_url
                    wd.find_element(By.CSS_SELECTOR, "a.next").click()
                    if WebDriverWait(wd, 30).until(EC.url_changes(url=cur_url)):
                        i=i+1
                except:
                    if WebDriverWait(wd, 5).until(EC.visibility_of_element_located((By.ID, "cookiescript_accept"))):
                        logging.info("Çerez Uyarısı Görüntülendi")
                        wd.find_element(By.ID, "cookiescript_accept").click()
                        cur_url=wd.current_url
                        wd.find_element(By.CSS_SELECTOR, "a.next").click()
                        if WebDriverWait(wd, 30).until(EC.url_changes(url=cur_url)):
                            i=i+1
                        logging.info("Çerez Uyarısı Kapatıldı")
            except:
                logging.info("NEXT Class buton bulunamadı")
                break
    return CurrentDF

wd= initialize_driver()
for link in links:
    logging.info("Kategori: {link}")
    df = pd.concat([df,pd.DataFrame(veri_al(link),columns = column)])
    
df.reset_index(inplace=True)
df.drop("index",axis=1,inplace=True)
df.to_csv(filename,sep=';',index=False,encoding="utf-8")