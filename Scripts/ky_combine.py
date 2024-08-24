import os
import pandas as pd
import json
from datetime import date
import logging

# Configure logging
from additional import log_combine, log_config

log_combine()
log_config(os.getenv('LOG_FILE'))

# Read existing dataset
existing_df = pd.read_csv('Data/KY_Datasets.csv', sep=';')
logging.info('Existing dataset loaded')

# Read all scraped datasets
df_list = []
for i in range(1, 5):  # Adjust the number of jobs as needed
    filename = f'KY_{i}.csv'
    df1 = pd.read_csv('Datasets/' + filename, sep=';')
    df_list.append(df1)
combined_df = pd.concat(df_list, ignore_index=True)
logging.info('Scraped datasets loaded')

# Combine all dataframes
final_df = pd.concat([existing_df, combined_df], ignore_index=True)
logging.info('Data combined')
final_df["Tarih"] = pd.to_datetime(final_df["Tarih"])
final_df['Date'] = final_df.Tarih.dt.date
logging.info('Date column converted to datetime')
final_df.drop_duplicates(keep="first", subset=["Kitap İsmi", "URL", "Date", "Fiyat"], inplace=True)
logging.info('Duplicates removed')
final_df = final_df.sort_values(['Kitap İsmi', 'Date', 'Fiyat'])
logging.info('Data sorted')
final_df.drop("Date", axis=1, inplace=True)
final_df.reset_index(inplace=True)
logging.info('Data index reset')
final_df.drop("index", axis=1, inplace=True)
logging.info('Data merged and cleaned')
logging.info(f"Total number of records: {len(final_df)}")

# Save the combined data
final_df.to_csv('Data/KY_Datasets.csv', sep=';', index=False, encoding="utf-8")
logging.info('Final dataset saved')

# Upload new dataset to Kaggle
try:
    dictionary = {'title': "kitap-yurdu-dataset", 'id': "furkanzeki/kitap-yurdu-dataset", 'resources': [{"path": "KY_Datasets.csv", "description": "KY_Datasets"}]}
    jsonString = json.dumps(dictionary, indent=4)
    with open("Data/dataset-metadata.json", "w") as f:
        f.write(jsonString)
    logging.info('Metadata JSON file created successfully')

    with open("Data/dataset-metadata.json", "r") as f:
        logging.info(f'Metadata JSON content: {f.read()}')
except Exception as e:
    logging.error(f'Error creating or reading metadata JSON file: {e}')

logging.info('Script completed')