import os
import pandas as pd
import json
import kaggle
from datetime import date
from kaggle.api.kaggle_api_extended import KaggleApi

# # Mevcut dataset'i okuma
existing_df = pd.read_csv('Data/BKM_Datasets.csv',sep=';')

existing_df.info()

#Tüm Scrap Edilen DF Okuma
df_list = []
for i in range(1, 5):  # Job sayısını ihtiyacınıza göre artırın
    filename = f'BKM_{i}.csv'
    df1 = pd.read_csv('Datasets/'+filename,sep=';')
    df_list.append(df1)
combined_df = pd.concat(df_list, ignore_index=True)


# İki DataFrame'i birleştirme
final_df = pd.concat([existing_df, combined_df], ignore_index=True)
final_df["Tarih"] = pd.to_datetime(final_df["Tarih"])
final_df['Date'] = final_df.Tarih.dt.date
final_df.drop_duplicates(keep="first",subset=["Kitap İsmi","URL","Date","Fiyat"],inplace=True)
final_df=final_df.sort_values(['Kitap İsmi','Date','Fiyat'])
final_df.drop("Date",axis=1,inplace=True)
final_df.reset_index(inplace=True)
final_df.drop("index",axis=1,inplace=True)

# Birleştirilen veriyi kaydetme
final_df.to_csv('BKM_Datasets.csv',sep=';',index=False,encoding="utf-8")

# Yeni dataset'i Kaggle'ye yükleme
dictionary = {'title':"bkm-book-dataset", 'id':"furkanzeki/bkm-book-dataset", 'resources':[{"path": "BKM_Datasets.csv","description":"BKM_Datasets"}]}
jsonString = json.dumps(dictionary, indent=4)
f = open("Datasets/dataset-metadata.json", "w")
f.write(jsonString)
f = open("Datasets/dataset-metadata.json", "r")
print(f.read())


# Dataset'i yükleme
def publish_to_kaggle(folder, message):
    api = KaggleApi()
    api.authenticate()

    api.dataset_create_version(
        folder=folder,
        version_notes=message
    )

prep_location = "Datasets"

print("--> Publish to Kaggle")
publish_to_kaggle(prep_location, str(date.today()))
print("Kaggle Upload Ok")
