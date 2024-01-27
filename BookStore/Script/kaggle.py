from kaggle.api.kaggle_api_extended import KaggleApi
from datetime import date
import os
import pandas as pd
import numpy as np
import requests

prep_location = 'Datasets'
filename = "Datasets/BKM_Datasets.csv"

def dataset_format():
    data = pd.read_csv(filename, sep=";")
    data["Fiyat"] = pd.to_numeric(data["Fiyat"])
    data["Tarih"] = pd.to_datetime(data['Tarih'], format="%Y-%m-%d %H:%M:%S")
    return data

def datasets_download():
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(
        dataset="furkanzeki/bookdataset", path=prep_location, unzip=True)
    print("Dosya İndirildi") 
    return dataset_format()


def publish_to_kaggle(folder, message):
    api = KaggleApi()
    api.authenticate()

    api.dataset_create_version(
        folder=folder,
        version_notes=message
    )

def datasets_upload():
    prep_location = '../Data'
    print("--> Publish to Kaggle")
    publish_to_kaggle(prep_location, str(date.today()))
    print("Kaggle Upload Ok")
    return "OK"
