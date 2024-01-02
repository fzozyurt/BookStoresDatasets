import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import date

direction="./BKM_other_data"
links = []
site = 'https://www.bkmkitap.com'

url = "https://www.bkmkitap.com/kategori-listesi"
response = requests.get(url,verify=False)
html_icerigi = response.content
soup = BeautifulSoup(html_icerigi, "html.parser")
kategori = soup.find_all("a", class_=["btn btn-default btn-upper"])
for a in range(len(kategori)):
    kategori[a] = str(site+"/"+(kategori[a]['href']))
    links.append(kategori[a])
    print(kategori[a])


def partion(direction,links=[],count=3):
    df = pd.DataFrame(links)
    df.reset_index(drop=True, inplace=True)
    df["Node"] = df.index.map(lambda x: x % count + 1)
    df.to_csv(direction+"/Kategori.csv", index=False)

partion(direction,links,5)

