import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import date

# Mevcut Veri İçe Aktarma

filename = "Datasets/BKM_Datasets.csv"
print(str(pd.to_datetime("today")))

# Yeni veri oluşturma
df = pd.DataFrame(columns=["Kitap İsmi", "Yazar", "Yayın Evi", "Fiyat",
                  "URL", "Platform", "Tarih", "Kapak Kucultulmus", "Kapak Resmi"])
links = []
site = 'https://www.bkmkitap.com'

# Kategori İçe Aktarma
url = "https://www.bkmkitap.com/kategori-listesi"
response = requests.get(url)
html_icerigi = response.content
soup = BeautifulSoup(html_icerigi, "html.parser")
kategori = soup.find_all("a", class_=["btn btn-default btn-upper"])
for a in range(len(kategori)):
    kategori[a] = str(site+"/"+(kategori[a]['href']))
    links.append(kategori[a])
    print(kategori[a])

# Yeni Veri Alma


def veri_al(i, link):
    url = link+"?pg="+str(i)
    response = requests.get(url)
    html_icerigi = response.content
    soup = BeautifulSoup(html_icerigi, "html.parser")
    fiyat = soup.find_all("div", {"class": "col col-12 currentPrice"})
    isim = soup.find_all(
        "a", {"class": "fl col-12 text-description detailLink"})
    yazar = soup.find_all("a", {"class": "fl col-12 text-title"})
    yayın = soup.find_all("a", {"class": "col col-12 text-title mt"})
    sayfa = soup.find_all(
        "a", {"class": "fl col-12 text-description detailLink"}, href=True)
    resim = soup.find_all('img', {'class': 'lazy stImage'})
    Bresim = soup.find_all('img', {'class': 'lazy stImage'})
    if i == 1:
        sayfasayi = soup.find_all(
            "div", {"class": "fr col-sm-12 text-center productPager"})
        sayfasayi = str(sayfasayi)
        words = re.findall(r'>\S+</a>', sayfasayi)
        for w in words:
            w = w.replace('>', '')
            w = w.replace('</a', '')
            w = w.split(",")
            if w != "...":
                list1.append(w[0])
                print("Listeye Eklenen Değer : "+str(w))
    for a in range(len(isim)):
        isim[a] = (isim[a].text).strip("\n").strip()
        yazar[a] = (yazar[a].text).strip("\n").strip()
        yayın[a] = (yayın[a].text).strip("\n").strip()
        fiyat[a] = (fiyat[a].text).strip("\n").replace("\nTL", " TL").strip()
        sayfa[a] = site+(sayfa[a]['href'])
        resim[a] = (resim[a]['data-src'])
        Bresim[a] = resim[a].replace('-K.jpg', '-O.jpg')
        liste.append([isim[a], yazar[a], yayın[a], fiyat[a], sayfa[a], "BKM Kitap",
                     pd.to_datetime("today"), resim[a], Bresim[a]])
    print("Sayfa No : "+str(i)+" İşlem OK")


# Veri Alma Fonksiyonunu Çalıştır
for link in links:
    print("Kategori : "+str(link))
    liste = []
    list1 = []
    i = 1
    veri_al(i, str(link))
    if list1 != []:
        i = i+1
        while i <= eval(list1[-1]):
            veri_al(i, str(link))
            i = i+1
    df = pd.concat([df, pd.DataFrame(liste, columns=["Kitap İsmi", "Yazar", "Yayın Evi",
                   "Fiyat", "URL", "Platform", "Tarih", "Kapak Kucultulmus", "Kapak Resmi"])])
    print("Kategori Ok : "+str(link))
df = df.drop_duplicates(subset=['URL', 'Fiyat', 'Platform', "Tarih"])
df.count()

# Fiyatın Sonundaki Parabirimi Sembolübü yeni Stuna Taşıyoruz
df[['Fiyat', 'ParaBirimi']] = df.Fiyat.str.rsplit(' ', n=1, expand=True)
df[['Fiyat', 'Kr']] = df.Fiyat.str.rsplit(',', n=1, expand=True)
df['Fiyat'] = df.Fiyat.str.replace("[$.]", "", regex=True)
df['Fiyat'] = df['Fiyat'] + "."+df['Kr']
df.drop("Kr", axis=1, inplace=True)

df["Fiyat"] = pd.to_numeric(df["Fiyat"])
df['Tarih'] = pd.to_datetime(df['Tarih'], format="%d.%m.%Y %H:%M:%S")

df.reset_index(inplace=True)
df.drop("index", axis=1, inplace=True)
print("İndex Resetlendi")


df.to_csv(filename, sep=';', index=False)
print("Dosya Güncellendi")
