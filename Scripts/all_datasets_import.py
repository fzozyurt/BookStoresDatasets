from kaggle.api.kaggle_api_extended import KaggleApi

prep_location = 'Datasets'+

api = KaggleApi()
api.authenticate()

KaggleApi.dataset_download_files(
    dataset="furkanzeki/bookdataset", path=prep_location, unzip=True)

print("Dosya İndirildi")
