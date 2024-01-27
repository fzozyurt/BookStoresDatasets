import pandas as pd
from BookStore.BKM.bkm_new_data import veri_al
from BookStore.Script.others import partion
from BookStore.Script.operation import URL_and_price_list,last_price_query
from  BookStore.Script.kaggle import datasets_download,datasets_upload
from BookStore.BKM.bkm_get_categori import get_category

def get_category():
    links=get_category() #Web Witesinden Kategorileri Çekiyoruz. Links Değişkenine Atıyoruz
    return {"categories_part_list": partion(links,5)}  # Çekilen Kategorileri Eş Parçaya Bölüyoruz ve Links Değişkenine Atıyoruz

def dataset_download():
    return datasets_download()

def dataset_upload():
    datasets_upload()

def web_scraping():
    return

def grupby_last_price_list(data):
    return URL_and_price_list(data)

def link_last_price_query(grup):
    return last_price_query(grup)

def get_product_data(links):
    for link in links:
        print("Kategori URL: "+str(link))
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
    return df