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

# ២. ការតភ្ជាប់ Database ថ្មី (Chat DB)
# ==========================================
chat_mongo_url = os.getenv("CHAT_MONGO_URL")
chat_db_name = "jobber_chat_db" # កំណត់ឈ្មោះ DB សម្រាប់ Chat

if chat_mongo_url:
    chat_client = MongoClient(chat_mongo_url)
    chat_db = chat_client[chat_db_name]
    print("✅ Chat Database Connected Successfully!")
else:
    # ករណីភ្លេចដាក់ Env វាជួយការពារកុំឱ្យ Error ដោយប្រើ DB ចាស់សិន
    chat_db = db

# ==========================================
# 🎯 ប្រកាស Collection ទាំងអស់នៅទីនេះតែម្តង!
# ==========================================

users_collection = collections("users")
refresh_tokens_collection = collections("refresh_tokens")
otps_collection = collections("otps")

# categories
categories_collection = collections("categories")

# Locations
provinces_collection = collections("job_provinces")
districts_collection = collections("job_districts")

# Profiles
seeker_profiles_collection = collections("seeker_profiles")
company_profiles_collection = collections("company_profiles")

# Master Data Collections
work_types_collection = collections("work_types")
employment_types_collection = collections("employment_types")
job_levels_collection = collections("job_levels")
education_levels_collection = collections("education_levels")
skills_collection = collections("skills")
industries_collection = collections("industries")

# employer
job_posts_collection = collections("job_posts")
job_applications_collection = collections("job_applications")

# Real-time Chat (Seeker <-> Employer)
conversations_collection = chat_db.get_collection("conversations")
chat_messages_collection = chat_db.get_collection("chat_messages")
device_tokens_collection = collections("device_tokens")

# interview 
interviews_collection = collections("interviews")

# saved jobs
saved_jobs_collection = db.get_collection("saved_jobs")

# notifications
notifications_collection = db.get_collection("notifications")

