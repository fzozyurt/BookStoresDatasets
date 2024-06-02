import json
from bs4 import BeautifulSoup
import requests
from Scripts.data_partitioning import data_partitioning


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
    
if __name__ == "__main__":
    scrape_categories()