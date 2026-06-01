import os
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from dotenv import load_dotenv

load_dotenv()

# Get the MongoDB connection string from environment variables
mongo_url = os.getenv("MONGO_URL")
mongo_db_name = os.getenv("MONGO_DB_NAME", "jobber_city_db")

if not mongo_url:
    raise ValueError("MONGO_URL is not set in the environment variables")

# Pass the full string directly to MongoClient
client = MongoClient(mongo_url)
db = client[mongo_db_name]

def collections(name: str):
    return db[name]

