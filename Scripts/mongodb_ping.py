from pymongo import MongoClient

hastname="localhost"
port=27017

client=MongoClient(hastname,port)
sonuc=client.admin.command('ping')

print(sonuc)
