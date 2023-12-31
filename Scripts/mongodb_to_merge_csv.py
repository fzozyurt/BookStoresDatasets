import os
import pandas as pd
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["BookDatabase"]
collection = db[os.environ["PROJECT_NAME"]]
format = "%Y-%m-%d %H:%M:%S"
filename=os.environ["FILE_LOC"]

#Collection da olan verileri data değişkenine alıyoruz
data = pd.DataFrame(list(collection.find()))
data.drop("_id",axis=1,inplace=True) 

data = pd.read_csv(filename, sep=";")
data["Fiyat"] = pd.to_numeric(data["Fiyat"])
data['Tarih'] = pd.to_datetime(data['Tarih'], format=format)
data.info()

df = pd.concat([pd.read_csv(filename, sep=";") , data]) #Data değişkeni ile eski verileri birleştiriyoruz
df["Fiyat"] = pd.to_numeric(df["Fiyat"])
df['Tarih'] = pd.to_datetime(df['Tarih'], format=format)
df.info()

df.to_csv(filename,sep=';',index=False,encoding="utf-8")  #Birleştirilen değişkeni eski dosya ile değiştiriyoruz