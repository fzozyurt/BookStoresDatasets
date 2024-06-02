import os
from kaggle.api.kaggle_api_extended import KaggleApi

def download_kaggle_dataset(dataset_name):
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(dataset_name, path='data', unzip=True)
    print(f'Dataset {dataset_name} has been downloaded and unzipped.')

if __name__ == "__main__":
    dataset_name = os.getenv('DATASET_NAME')
    if dataset_name:
        download_kaggle_dataset(dataset_name)
    else: print("Dataset Value Is Empty")