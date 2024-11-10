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

def log_combine():
    # Log dosyalarının bulunduğu dizin
    log_directory = 'logs'
    # Birleştirilecek log dosyasının adı
    combined_log_file = 'logs/KY.log'

    # Birleştirilmiş log dosyasını oluşturun veya var olanı temizleyin
    with open(combined_log_file, 'w', encoding='utf-8') as outfile:
        for log_file in os.listdir(log_directory):
            if log_file.endswith('.log') and log_file.startswith('KY'):  # Sadece .log uzantılı ve KY ile başlayan dosyaları birleştir
                with open(os.path.join(log_directory, log_file), 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')  # Dosyalar arasında boşluk bırakmak için

    print(f'Log dosyaları {combined_log_file} dosyasında birleştirildi.')