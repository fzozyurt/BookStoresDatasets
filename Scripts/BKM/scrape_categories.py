import json
from bs4 import BeautifulSoup
import requests
import math
import numpy as np


def scrape_categories():
    links = []
    site = 'https://www.bkmkitap.com'

    # Kategori İçe Aktarma
    url = "https://www.bkmkitap.com/kategori-listesi"
    response = requests.get(url)
    html_icerigi = response.content
    soup = BeautifulSoup(html_icerigi, "html.parser")
    kategori = soup.find_all("a", class_=["btn btn-default btn-upper"])
    for a in range(len(kategori)):
        links.append({'name': str(kategori[a].text), 'url': str(site+"/"+(kategori[a]['href']))})
        print({'name': str(kategori[a].text), 'url': str(site+"/"+(kategori[a]['href']))})

    data_partitioning(links)

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

    
# def data_partitioning(links):
#     total_jobs = 5
#     chunk_size = math.ceil(len(links) / total_jobs)

#     for i in range(total_jobs):
#         start = i * chunk_size
#         end = start + chunk_size
#         chunk = links[start:end]

#         with open(f'categories_{i + 1}.json', 'w', encoding='utf-8') as f:
#             json.dump(chunk, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_categories()