import logging
import json
import numpy as np
import os

ID=os.getenv('ID')

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
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(logging.WARNING)  # Sadece WARNING ve ERROR seviyesindeki logları dosyaya yaz

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)  # Konsola sadece WARNING ve ERROR seviyesindeki logları yaz

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            file_handler,
            stream_handler
        ]
    )
def log_combine():
    # Log dosyalarının bulunduğu dizin
    log_directory = 'logs'
    # Birleştirilecek log dosyasının adı
    combined_log_file = f'logs/{ID}.log'

    # Birleştirilmiş log dosyasını oluşturun veya var olanı temizleyin
    with open(combined_log_file, 'w', encoding='utf-8') as outfile:
        all_files_empty = True
        for log_file in os.listdir(log_directory):
            if log_file.endswith('.log') and log_file.startswith(ID):  # Sadece .log uzantılı ve ID değeri ile başlayan dosyaları birleştir
                with open(os.path.join(log_directory, log_file), 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    if content.strip():  # Dosya boş değilse
                        all_files_empty = False
                    outfile.write(content)
                    outfile.write('\n')  # Dosyalar arasında boşluk bırakmak için

        if all_files_empty:
            outfile.write('ERROR seviyesinde herhangi bir hata alınmadan süreç sonlandırıldı\n')

    print(f'Log dosyaları {combined_log_file} dosyasında birleştirildi.')