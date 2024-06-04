import json
from bs4 import BeautifulSoup
import math

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
    total_jobs = 5
    chunk_size = math.ceil(len(links) / total_jobs)

    for i in range(total_jobs):
        start = i * chunk_size
        end = start + chunk_size
        chunk = links[start:end]

        with open(f'categories_{i + 1}.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_categories()

