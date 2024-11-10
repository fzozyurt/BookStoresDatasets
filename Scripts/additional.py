import logging
import json
import numpy as np
import os

def data_partitioning(links):
    # Verileri numpy array'ine çevirme ve karıştırma
    data_array = np.array(links)
    np.random.shuffle(data_array)
    logging.debug("Data shuffled")

    # Veriyi 5 parçaya bölmeden önce verilerin sıralarını karıştırma
    np.random.shuffle(data_array)
    logging.debug("Data shuffled again before splitting")

    # Veriyi 5 parçaya bölme
    split_data = np.array_split(data_array, 5)
    logging.info("Data split into 5 parts")

    # Parçaları ayrı JSON dosyalarına yazma
    for i, chunk in enumerate(split_data):
        file_name = f'categories_{i + 1}.json'
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(chunk.tolist(), file, ensure_ascii=False, indent=4)
            logging.info("Successfully wrote data to %s", file_name)
        except IOError as e:
            logging.error("Error writing data to %s: %s", file_name, str(e))

def log_config(file_name, log_format="%(asctime)s - %(levelname)s - %(message)s"):
    file_name = "./logs/" + file_name
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(file_name),
            logging.StreamHandler()
        ]
    )

# def log_combine():
#     ID=os.getenv('ID')

#     # Log dosyalarını birleştirme
#     log_files = [f'logs/{ID}_{i}.log' for i in range(1, 6)]
#     combined_logs = []

#     for log_file in log_files:
#         with open(log_file, 'r') as file:
#             lines = file.readlines()
#             combined_logs.extend(lines)

#     # Mevcut BKM.log dosyasına ekleme
#     with open('logs/BKM.log', 'a') as outfile:
#         for log in combined_logs:
#             outfile.write(log.strip() + '\n')  # Her log girişinden sonra bir satır boşluk ekle

#     # Okunan log dosyalarını silme
#     for log_file in log_files:
#         os.remove(log_file)