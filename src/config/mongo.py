# from pymongo import MongoClient
# import os
# from dotenv import load_dotenv

# load_dotenv()

# MONGO_USERNAME = os.getenv("MONGO_USERNAME")
# MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
# MONGO_HOST = os.getenv("MONGO_HOST")
# MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

# url = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/Jobber_City?authSource=admin"
# client = MongoClient(url)

# def collections(name):
#     return client["Jobber_City_data"][name]


import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Read the public connection string directly
mongo_url = os.getenv("MONGO_PUBLIC_URL")

if not mongo_url:
    raise ValueError("MONGO_PUBLIC_URL is not set in the environment variables")

# Pass the full string directly to MongoClient
client = MongoClient(mongo_url)

def collections(name):
    return client["Jobber_City_data"][name]

