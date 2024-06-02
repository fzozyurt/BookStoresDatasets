import json
from bs4 import BeautifulSoup
import requests
import math


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