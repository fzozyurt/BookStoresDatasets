import math
import json
import numpy as np

# def data_partitioning(links):
#     total_jobs = 5
#     chunk_size = math.ceil(len(links) / total_jobs)

#     for i in range(total_jobs):
#         start = i * chunk_size
#         end = start + chunk_size
#         chunk = links[start:end]

#         with open(f'categories_{i + 1}.json', 'w', encoding='utf-8') as f:
#             json.dump(chunk, f, ensure_ascii=False, indent=4)

def data_partitioning(links):
    # Verileri numpy array'ine çevirme ve karıştırma
    data_array = np.array(links)
    np.random.shuffle(data_array)

    # Veriyi 5 parçaya bölme
    split_data = np.array_split(data_array, 5)

    # Parçaları ayrı JSON dosyalarına yazma
    for i, chunk in enumerate(split_data):
        with open(f'categories_{i + 1}.json', 'w',encoding='utf-8') as file:
            json.dump(chunk.tolist(), file,ensure_ascii=False, indent=4)