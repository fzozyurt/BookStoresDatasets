import os
from kaggle.api.kaggle_api_extended import KaggleApi

def dataset_download(prep_location='Datasets',kdataset=os.environ["DATASET_PATH"]):

    api = KaggleApi()
    api.authenticate()

    api.dataset_download_files(
        dataset=kdataset, path=prep_location, unzip=True)
    return "Dosya İndirildi"
