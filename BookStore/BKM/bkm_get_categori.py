import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import date

links = []
site = "https://www.bkmkitap.com"


def get_category():
    url = "https://www.bkmkitap.com/kategori-listesi"
    response = requests.get(url,verify=False)
    html_icerigi = response.content
    soup = BeautifulSoup(html_icerigi, "html.parser")
    kategori = soup.find_all("a", class_=["btn btn-default btn-upper"])
    for a in range(len(kategori)):
        kategori[a] = str(site+"/"+(kategori[a]['href']))
        links.append(kategori[a])
        print(kategori[a])
    return links
