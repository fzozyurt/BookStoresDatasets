import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re

# Mevcut Veri İçe Aktarma

filename = "Datasets/BKM_Datasets.csv"
data = pd.read_csv(filename, sep=";")

data.info()

data["Fiyat"] = pd.to_numeric(data["Fiyat"])
data['Tarih'] = pd.to_datetime(data['Tarih'])

data.info()

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

# Mevcut Verideki En Güncel Fiyatı Sorgulama


def son_fiyat_sorgu(link):
    URL_filter_data = grup.query("URL ==@link")["Fiyat"]
    return URL_filter_data


grup = data.groupby(['URL']).agg(Tarih=('Tarih', np.max))
grup = pd.merge(grup, data[['URL', 'Tarih', 'Fiyat']],
                how='left', on=['URL', 'Tarih'])

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
                     pd.to_datetime("today").date(), resim[a], Bresim[a]])
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
df['Tarih'] = pd.to_datetime(df['Tarih'])

df.reset_index(inplace=True)
df.drop("index", axis=1, inplace=True)
print("İndex Resetlendi")

# Standart Sapması 0 olanlar silinir
Std_Data = pd.concat([df, grup]).groupby('URL').agg({'Fiyat': 'std'})
Std_Data.to_csv("standartsapma.csv", sep=';')
Std_Data = Std_Data[Std_Data["Fiyat"] == 0]
df.drop(labels=df[df.URL.isin(list(Std_Data.index))].index,
        axis=0, inplace=True)

data = pd.concat([data, df])

data.to_csv(filename, sep=';', index=False, encoding="utf-8")
print("Dosya Güncellendi")
