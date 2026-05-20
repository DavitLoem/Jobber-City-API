from datetime import datetime
from bson import ObjectId
# 📝 ហៅ collections ចេញពីឯកសារ config របស់បង
from src.config.mongo import collections 

def get_all_expertises_service() -> list:
    """[GET] ទាញយក Expertise ទាំងអស់ពី MongoDB"""
    try:
        expertise_col = collections("Expertise")
        stored_expertises = expertise_col.find({"is_active": True})
        return [doc["expertise_name"] for doc in stored_expertises]
    except Exception as e:
        print(f"Error getting expertises: {e}")
        return []

def store_validated_expertise_service(expertise_name: str) -> dict:
    """[POST] បញ្ចូល Expertise ថ្មីទៅក្នុង database"""
    try: 
        expertise_col = collections("Expertise")
        
        # ឆែកកុំឱ្យជាន់គ្នា
        existing_exp = expertise_col.find_one({"expertise_name": expertise_name})
        if existing_exp:
            return {
                "success": False,
                "message": f"Expertise '{expertise_name}' already in database."
            }

        expertise_data = {
            "expertise_name": expertise_name, # ✅ កែពីចាស់ឱ្យត្រូវនឹងឈ្មោះ Parameter 
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True
        }
        result = expertise_col.insert_one(expertise_data)

        return {
            "success": True,
            "message": f"Expertise '{expertise_name}' stored successfully!",
            "expertise_id": str(result.inserted_id)
        }
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}

def update_expertise_service(exp_id: str, new_expertise_name: str) -> dict:
    """[PUT] កែប្រែឈ្មោះ Expertise តាមរយៈ ID"""
    try:
        expertise_col = collections("Expertise")
        result = expertise_col.update_one(
            {"_id": ObjectId(exp_id)},
            {"$set": {
                "expertise_name": new_expertise_name,
                "updated_at": datetime.now()
            }}
        )
        if result.matched_count == 0:
            return {"success": False, "message": "Expertise ID not found."}
        return {"success": True, "message": f"Expertise updated to '{new_expertise_name}' successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}

def delete_expertise_service(exp_id: str) -> dict:
    """[DELETE] លុប Expertise ចេញពី Database តាមរយៈ ID"""
    try:
        expertise_col = collections("Expertise")
        result = expertise_col.delete_one({"_id": ObjectId(exp_id)})
        if result.deleted_count == 0:
            return {"success": False, "message": "Expertise ID not found."}
        return {"success": True, "message": "Expertise deleted successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Database Error: {str(e)}"}