import os
import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import date

# Mevcut Veri İçe Aktarma

matrix=os.getenv('matrix_id')
filename = "Dataset/BKM_"+matrix+".csv"

links=[]
# JSON dosyasını oku ve Kategorileri links değerine yaz
categories_file = os.getenv('categories_file')
with open(categories_file, 'r') as f:
    data = json.load(f)
for categori in data:
    links.append(categori["url"])

columns=["Kitap İsmi", "Yazar", "Yayın Evi", "Fiyat",
                  "URL", "Platform", "Tarih", "Kapak Kucultulmus", "Kapak Resmi"]

#Dataset Dosyasını Oku
data = pd.DataFrame(columns=columns)
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
    
def get_data(soup):
    listeData=[]
    try:
        category=soup.find_all('span', property='name')[-1].text
        urunler = soup.find_all("div", class_="productItem")
        for urun in urunler:
            title= urun.find("a", class_="fl col-12 text-description detailLink").text.strip()
            author = urun.find("a", class_="fl col-12 text-title").text.strip()
            publisher = urun.find("a", class_="col col-12 text-title mt").text.strip()
            price = urun.find("div", class_="col col-12 currentPrice").text.strip().replace("\nTL", "").strip()
            img = urun.find("img", class_="lazy stImage")["data-src"]
            url = f"https://www.bkmkitap.com{urun.find('a', class_='fl col-12 text-description detailLink')['href']}"
            if tur_degistir(price)!=float(son_fiyat_sorgu(url)):
                listeData.append([title, author, publisher, tur_degistir(price), url, "BKM Kitap",datetime.now(timezone('UTC')).astimezone(timezone('Asia/Istanbul')).strftime(format), img,img.replace('-K.jpg', '-O.jpg')])    
    except:
        print("Data Okunamadı")
    return listeData

def get_sayfa_sayisi(soup):
    try:
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
        return int(sayi[-1])
    except:
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

for link in links:
    print("Kategori : "+link)
    data = pd.concat([data,pd.DataFrame(veri_al(link),columns = column)])

data.reset_index(inplace=True)
data.drop("index",axis=1,inplace=True)
data.to_csv(filename,sep=';',index=False,encoding="utf-8")