import logging
import json
import numpy as np
import os

from Scripts.logging_utils import setup_logging

ID = os.getenv('ID')


def data_partitioning(links):
    data_array = np.array(links)
    np.random.shuffle(data_array)
    logging.debug("Data shuffled")

    np.random.shuffle(data_array)
    logging.debug("Data shuffled again before splitting")

    split_data = np.array_split(data_array, 5)
    logging.info("Data split into 5 parts")

    for i, chunk in enumerate(split_data):
        file_name = f'categories_{i + 1}.json'
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(chunk.tolist(), file, ensure_ascii=False, indent=4)
            logging.info("Successfully wrote data to %s", file_name)
        except IOError as e:
            logging.error("Error writing data to %s: %s", file_name, str(e))


def log_config(file_name, log_format="%(asctime)s - %(levelname)s - %(message)s"):
    setup_logging(log_file=file_name, log_format=log_format)


def log_combine():
    log_directory = 'logs'
    combined_log_file = f'logs/{ID}_errors.log'

    with open(combined_log_file, 'w', encoding='utf-8') as outfile:
        all_files_empty = True
        for log_file in os.listdir(log_directory):
            if log_file.endswith('.log') and log_file.startswith(ID):
                with open(os.path.join(log_directory, log_file), 'r', encoding='utf-8') as infile:
                    for line in infile:
                        if 'WARNING' in line or 'ERROR' in line:
                            all_files_empty = False
                            outfile.write(line)

        if all_files_empty:
            outfile.write('ERROR seviyesinde herhangi bir hata alinmadan surec sonlandirildi\n')

    print(f'Log dosyalari {combined_log_file} dosyasinda birlestirildi.')
