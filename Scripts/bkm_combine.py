import os
import pandas as pd
import json
from datetime import date
import logging


# Configure logging
from additional import log_combine, log_config

log_config(os.getenv('LOG_FILE'))

# Mevcut dataset'i okuma
existing_df = pd.read_csv('Data/BKM_Datasets.csv', sep=';')
logging.info('Existing dataset loaded')

# Tüm Scrap Edilen DF Okuma
df_list = []
for i in range(1, 5):  # Job sayısını ihtiyacınıza göre artırın
    filename = f'BKM_{i}.csv'
    df1 = pd.read_csv('Datasets/' + filename, sep=';')
    df_list.append(df1)
combined_df = pd.concat(df_list, ignore_index=True)
logging.info('Scraped datasets loaded')

# İki DataFrame'i birleştirme
final_df = pd.concat([existing_df, combined_df], ignore_index=True)
logging.debug('Data combined')
final_df["Tarih"] = pd.to_datetime(final_df["Tarih"])
final_df['Date'] = final_df.Tarih.dt.date
logging.debug('Date column converted to datetime')
final_df.drop_duplicates(keep="first", subset=["Kitap İsmi", "URL", "Date", "Fiyat"], inplace=True)
logging.debug('Duplicates removed')
final_df = final_df.sort_values(['Kitap İsmi', 'Date', 'Fiyat'])
logging.debug('Data sorted')
final_df.drop("Date", axis=1, inplace=True)
final_df.reset_index(inplace=True)
logging.debug('Data index reset')
final_df.drop("index", axis=1, inplace=True)
logging.info('Data merged and cleaned')
logging.debug(f"Total number of records: {len(final_df)}")

# Birleştirilen veriyi kaydetme
final_df.to_csv('Data/BKM_Datasets.csv', sep=';', index=False, encoding="utf-8")
logging.debug('Final dataset saved')

# Yeni dataset'i Kaggle'ye yükleme
dictionary = {'title': "bkm-book-dataset", 'id': "furkanzeki/bkm-book-dataset",
              'resources': [{"path": "BKM_Datasets.csv", "description": "BKM_Datasets"}]}
jsonString = json.dumps(dictionary, indent=4)
f = open("Data/dataset-metadata.json", "w")
f.write(jsonString)
f = open("Data/dataset-metadata.json", "r")
logging.debug('Dataset metadata file created')

log_combine()

logging.info('Script completed')
logging.shutdown()