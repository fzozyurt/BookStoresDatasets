from kaggle.api.kaggle_api import KaggleApi

prep_location = 'Datasets'

KaggleApi.datasets_download_file(
    "furkanzeki/bookdataset", path=prep_location, unzip=True)

print("Dosya İndirildi")
