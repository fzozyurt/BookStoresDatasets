import os
import pandas as pd
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["BookDatabase"]
collection = db[os.environ["PROJECT_NAME"]]

def send_mongodb(df=[]):
    if df!=[]:
        df.reset_index(inplace=True)
        data_dict = df.to_dict("records")
        collection.insert_many(data_dict)