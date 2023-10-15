from kaggle.api.kaggle_api_extended import KaggleApi

prep_location = '../Datasets'

kaggle.api.dataset_download_files(
    "furkanzeki/bookdataset", path=prep_location, unzip=True)
