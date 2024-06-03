import pandas as pd
import json
import kaggle

# CSV dosyalarını birleştirme
df_list = []
for i in range(1, 5):  # Job sayısını ihtiyacınıza göre artırın
    filename = f'BKM_{i}.csv'
    df = pd.read_csv('Datasets/'+filename)
    df_list.append(df)

combined_df = pd.concat(df_list, ignore_index=True)

# # Mevcut Kaggle dataset'ini indir
# dataset_owner = 'kullanici_adiniz'
# dataset_name = 'dataset_adiniz'
# kaggle.api.dataset_download_files(f'{dataset_owner}/{dataset_name}', path='.', unzip=True)

# # Mevcut dataset'i okuma
# existing_df = pd.read_csv('mevcut_dataset.csv')

# # İki DataFrame'i birleştirme
# final_df = pd.concat([existing_df, combined_df], ignore_index=True)

# Birleştirilen veriyi kaydetme
combined_df.to_csv('BKM_Datasets.csv',sep=';',index=False,encoding="utf-8")

# Yeni dataset'i Kaggle'ye yükleme

dictionary = {'title':"bkm-book-dataset", 'id':"furkanzeki/bkm-book-dataset", 'resources':[{"path": "BKM_Datasets.csv","description":"BKM_Datasets"}]}
jsonString = json.dumps(dictionary, indent=4)
f = open("Datasets/dataset-metadata.json", "w")
f.write(jsonString)
f = open("Datasets/dataset-metadata.json", "r")
print(f.read())

from datetime import date
from kaggle.api.kaggle_api_extended import KaggleApi
# Dataset'i yükleme
def publish_to_kaggle(folder, message):
    api = KaggleApi()
    api.authenticate()

    api.dataset_create_version(
        folder=folder,
        version_notes=message
    )

prep_location = "Datasets"

print("--> Publish to Kaggle")
publish_to_kaggle(prep_location, str(date.today()))
print("Kaggle Upload Ok")
