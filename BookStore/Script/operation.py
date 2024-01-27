import os
import pandas as pd
import numpy as np
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import date
import airflow
from airflow.models import XCom

# Mevcut Verideki En Son Fiyatı Sorgulama İçin liste Hazırlama

def URL_and_price_list(data):
    grup = data.groupby(['URL']).agg(Tarih=('Tarih', np.max))
    grup = pd.merge(grup, data[['URL', 'Tarih', 'Fiyat']],
                    how='left', on=['URL', 'Tarih'])
    return grup

def last_price_query(link,grup):
    URL_filter_data = grup.query("URL ==@link")["Fiyat"]
    return URL_filter_data