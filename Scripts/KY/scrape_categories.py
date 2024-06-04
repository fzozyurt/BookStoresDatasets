import json
from bs4 import BeautifulSoup
import math
import numpy as np

from Selenium import initialize_driver


def scrape_categories():
    links = []

    # Kategori İçe Aktarma
    url = "https://www.kitapyurdu.com/index.php?route=product/category"

    wd= initialize_driver()
    wd.get(url)
    html_icerigi = wd.page_source
    soup = BeautifulSoup(html_icerigi,"html.parser")
    kategori = soup.find_all("a",class_=["category-item"])
    for a in range(len(kategori)):
        links.append({'name': kategori[a].text.strip(), 'url': str((kategori[a]['href']))})
        print({'name': kategori[a].text.strip(), 'url': str((kategori[a]['href']))})

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

if __name__ == "__main__":
    scrape_categories()

