from datetime import datetime
from bson import ObjectId
from src.model.cities import CambodianCity
# 📝 ត្រូវប្រាកដថា import collections ឱ្យចំកន្លែងដែលបងបានបង្កើតវា
# ឧទាហរណ៍៖
from src.config.mongo import collections


def get_all_stored_cities_service() -> list:
    try:
        city_col = collections("Cities")
        # ទាញយក Record ទាំងអស់ដែលសកម្ម (is_active: True)
        stored_cities = city_col.find({"is_active": True})
        
        # ចាប់យកតែឈ្មោះ city_name មកធ្វើជា List 
        cities_list = [doc["city_name"] for doc in stored_cities]
        return cities_list
    except Exception as e:
        print(f"Error fetching from DB: {str(e)}")
        return []

def store_validated_city_service(city_name: str) -> dict:
    try:
        # ហៅប្រើប្រាស់ collection ឈ្មោះ "validated_cities"
        city_col = collections("Cities")
        
        # ឆែកមើលក្រុងដែលមានស្រាប់ ដើម្បីការពារកុំឱ្យទិន្នន័យជាន់គ្នា
        existing_city = city_col.find_one({"city_name": city_name})
        if existing_city:
            return {
                "success": False,
                "message": f"City '{city_name}' already exists in database."
            }
            
        # រៀបចំទម្រង់ទិន្នន័យសម្រាប់លោតចូល MongoDB
        city_data = {
            "city_name": city_name,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True
        }
        
        # 📥 ដំណើរការ POST/Insert ចូល MongoDB របស់បង
        result = city_col.insert_one(city_data)
        
        return {
            "success": True,
            "message": f"City '{city_name}' stored into database successfully!",
            "city_id": str(result.inserted_id) # បម្លែង ObjectId ទៅជា String ដើម្បីបោះទៅឱ្យ Client
        }
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}


def update_city_service(city_id: str, new_city_name: str) -> dict:
    try:
        city_col = collections("Cities")
        
        # 📝 ដំណើរការ PUT/Update ទៅកាន់ MongoDB តាមរយៈ ObjectId(city_id)
        result = city_col.update_one(
            {"_id": ObjectId(city_id)},
            {"$set": {
                "city_name": new_city_name,
                "updated_at": datetime.now()
            }}
        )
        
        if result.matched_count == 0:
            return {"success": False, "message": "City ID not found in database."}
            
        return {"success": True, "message": f"City updated to '{new_city_name}' successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}


def delete_city_service(city_id: str) -> dict:
    try:
        city_col = collections("Cities")
        
        # 🗑️ ដំណើរការ DELETE ចេញពី MongoDB
        result = city_col.delete_one({"_id": ObjectId(city_id)})
        
        if result.deleted_count == 0:
            return {"success": False, "message": "City ID not found in database."}
            
        return {"success": True, "message": "City deleted from database successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}