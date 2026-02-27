import os
import os
import logging
from kaggle.api.kaggle_api_extended import KaggleApi

from Scripts.logging_utils import setup_logging
import argparse

setup_logging(log_file=os.getenv('LOG_FILE'))

def download_kaggle_dataset(dataset_name):
    logging.info(f"Starting download for dataset: {dataset_name}")
    api = KaggleApi()
    api.authenticate()
    logging.info("Authenticated with Kaggle API")

    try:
        api.dataset_download_files(dataset_name, path='Data', unzip=True)
        logging.info(f"Dataset {dataset_name} has been downloaded and unzipped.")
    except Exception as e:
        logging.error(f"Error downloading dataset {dataset_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download a dataset from Kaggle.')
    parser.add_argument('--dataset_name', type=str, default=os.getenv('DATASET_NAME'), help='Name of the dataset to download')
    args = parser.parse_args()

    dataset_name = args.dataset_name
    logging.info("Script started")
    logging.info(f"Dataset Name: {dataset_name}")

    if dataset_name:
        download_kaggle_dataset(dataset_name)
    else:
        logging.error("Dataset Name is empty")

    logging.info("Script finished")
