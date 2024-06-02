import math
import json

def data_partitioning(links):
    total_jobs = 5
    chunk_size = math.ceil(len(links) / total_jobs)

    for i in range(total_jobs):
        start = i * chunk_size
        end = start + chunk_size
        chunk = links[start:end]

        with open(f'categories_{i + 1}.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=4)