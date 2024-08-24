from datetime import date
import logging
import os
from kaggle.api.kaggle_api_extended import KaggleApi


from additional import log_config

log_config(os.getenv('LOG_FILE'))

def publish_to_kaggle(folder, message):
    logging.info(f"Starting publish_to_kaggle with folder: {folder} and message: {message}")
    api = KaggleApi()
    api.authenticate()
    logging.info("Authenticated with Kaggle API")

    try:
        api.dataset_create_version(
            folder=folder,
            version_notes=message
        )
        logging.info("Dataset version created successfully")
    except Exception as e:
        logging.error(f"Error creating dataset version: {e}")

if __name__ == "__main__":
    prep_location = 'Data'
    logging.info("Script started")

    print("--> Publish to Kaggle")
    logging.info("Publishing to Kaggle")
    publish_to_kaggle(prep_location, str(date.today()))
    logging.info("Kaggle Upload Ok")
    print("Kaggle Upload Ok")
    logging.info("Script finished")