from datetime import date
import logging
import os

from Scripts.additional import log_config

def publish_to_kaggle(folder, message):
    # Import kaggle here to avoid authentication issues on module load
    from kaggle.api.kaggle_api_extended import KaggleApi
    
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
    log_config(os.getenv('LOG_FILE'))
    
    prep_location = 'Data'
    logging.info("Script started")

    print("--> Publish to Kaggle")
    logging.info("Publishing to Kaggle")
    publish_to_kaggle(prep_location, str(date.today()))
    logging.info("Kaggle Upload Ok")
    print("Kaggle Upload Ok")
    logging.info("Script finished")