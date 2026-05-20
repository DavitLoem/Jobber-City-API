from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

url = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/Jobber_City?authSource=admin"
client = MongoClient(url)

def collections(name):
    return client["Jobber_City_data"][name]

