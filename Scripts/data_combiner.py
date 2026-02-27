#!/usr/bin/env python3
import os
import pandas as pd
import json
import logging
from datetime import date
import argparse
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def combine_dataset(site_name, job_count=5):
    """
    Combine multiple chunk datasets into a single file
    """
    logging.info(f"Starting combine process for {site_name}")
    
    # Read existing dataset
    try:
        existing_df = pd.read_csv(f'Data/{site_name}_Datasets.csv', sep=';')
        logging.info(f'Existing dataset loaded with {len(existing_df)} records')
    except Exception as e:
        logging.warning(f"Error loading existing dataset: {e}")
        logging.info("Creating new dataset")
        # Create empty dataframe with correct columns
        if site_name == "KY":
            columns = ["Kitap İsmi", "Yazar", "Yayınevi", "", "", "", "Kategori", "Fiyat", "URL",
                       "Site", "Tarih", "Resim", "Puan", "Değerlendirme Sayısı", "NLP Data"]
        else:  # BKM
            columns = ["Kitap İsmi", "Yazar", "Yayınevi", "Fiyat", "URL", "Site", "Tarih", 
                       "Resim", "ResimBüyük", "Kategori"]
        existing_df = pd.DataFrame(columns=columns)
    
    # Read all scraped datasets
    df_list = []
    try:
        for i in range(1, job_count + 1):
            filename = f'Dataset/{site_name}_{i}.csv'
            try:
                df = pd.read_csv(filename, sep=';')
                df_list.append(df)
                logging.info(f"Loaded dataset chunk {filename} with {len(df)} records")
            except Exception as e:
                logging.warning(f"Could not load dataset chunk {filename}: {e}")
        
        if not df_list:
            logging.error("No dataset chunks could be loaded")
            return False
            
        combined_df = pd.concat(df_list, ignore_index=True)
        logging.info(f'Combined {len(combined_df)} records from scraped datasets')
    except Exception as e:
        logging.error(f"Error combining scraped datasets: {e}")
        return False
    
    # Combine all dataframes
    try:
        final_df = pd.concat([existing_df, combined_df], ignore_index=True)
        logging.info('Data combined')
        
        # Process the combined data
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
        
        if "index" in final_df.columns:
            final_df.drop("index", axis=1, inplace=True)
        logging.info('Data merged and cleaned')
        logging.info(f"Total number of records: {len(final_df)}")
        
        # Save the combined data
        final_df.to_csv(f'Data/{site_name}_Datasets.csv', sep=';', index=False, encoding="utf-8")
        logging.info('Final dataset saved')
        
        # Create metadata for Kaggle
        try:
            if site_name == "KY":
                dictionary = {
                    'title': "kitap-yurdu-dataset", 
                    'id': "furkanzeki/kitap-yurdu-dataset", 
                    'resources': [{"path": "KY_Datasets.csv", "description": "KY_Datasets"}]
                }
            else:  # BKM
                dictionary = {
                    'title': "bkm-book-dataset", 
                    'id': "furkanzeki/bkm-book-dataset",
                    'resources': [{"path": "BKM_Datasets.csv", "description": "BKM_Datasets"}]
                }
                
            jsonString = json.dumps(dictionary, indent=4)
            with open("Data/dataset-metadata.json", "w") as f:
                f.write(jsonString)
            logging.info('Metadata JSON file created successfully')
        except Exception as e:
            logging.error(f'Error creating metadata JSON file: {e}')
        
        return True
    except Exception as e:
        logging.error(f"Error processing combined data: {e}")
        return False


if __name__ == "__main__":
    from Scripts.additional import log_combine
    from Scripts.logging_utils import setup_logging
    
    parser = argparse.ArgumentParser(description='Combine scraped datasets.')
    parser.add_argument('site', choices=['KY', 'BKM'], help='Site datasets to combine (KY or BKM)')
    parser.add_argument('--job-count', type=int, default=5, help='Number of job chunks to combine')
    parser.add_argument('--log-file', type=str, default=None, help='Log file path')
    
    args = parser.parse_args()
    
    log_file = args.log_file or f"{args.site}_combine.log"
    setup_logging(log_file=log_file)
    
    os.environ['ID'] = args.site  # For log_combine function
    
    if combine_dataset(args.site, args.job_count):
        try:
            log_combine()
        except Exception as e:
            logging.error(f"Error combining logs: {e}")
        logging.info('Combine process completed successfully')
    else:
        logging.error('Combine process failed')
