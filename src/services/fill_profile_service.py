from src.core.mongo import collections
from datetime import datetime
from src.model.fill_profile_model import FillProfile
from src.services.auth_service import check_email_uniqueness_for_update


def fill_profile_service(profile_data: FillProfile, image_url: str = None, image_public_id: str = None):
    # ១. ស្វែងរក User តាមរយៈ Email នៅក្នុងគ្រប់ collections
    collections_to_check = ["employee", "employer", "users"]
    user = None
    user_col = None
    
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        user = current_col.find_one({"email": profile_data.email})
        if user:
            user_col = current_col
            break
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    # ២. Delete old image from Cloudinary if exists and new image is provided
    if image_url and image_public_id and user.get("image_public_id"):
        try:
            from src.utils.cloudinary import delete_image
            delete_image(user["image_public_id"])
        except Exception as e:
            print(f"[ERROR] Failed to delete old image: {e}")
        
    # ៣. រៀបចំទិន្នន័យថ្មីសម្រាប់ Update ចូល Database
    update_data = {
        "fullname": profile_data.fullname,
        "nickname": profile_data.nickname,
        "date_of_birth": datetime.combine(profile_data.date_of_birth, datetime.min.time()),
        "phone": profile_data.phone,
        "gender": profile_data.gender,
        "is_profile_completed": True, 
        "updated_at": datetime.now()
    }
    
    # ៤. Add image data if provided
    if image_url and image_public_id:
        update_data["image"] = image_url
        update_data["image_public_id"] = image_public_id
    
    # ៥. ធ្វើការ Update ទិន្នន័យទៅក្នុង Database
    user_col.update_one(
        {"email": profile_data.email}, 
        {"$set": update_data}
    )
    
    # ៦. ទាញយកទិន្នន័យដែលទើប Update រួចមកវិញដើម្បី Return
    updated_user = user_col.find_one({"email": profile_data.email})
    
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])
        updated_user.pop("password", None)
        
    return {"success": True, "user": updated_user}


def get_profile_service(email: str):
    """Get user profile by email"""
    collections_to_check = ["employee", "employer", "users"]
    
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        user = current_col.find_one({"email": email})
        
        if user:
            user["_id"] = str(user["_id"])
            user.pop("password", None)
            
            if "date_of_birth" in user and user["date_of_birth"]:
                user["date_of_birth"] = user["date_of_birth"].strftime("%Y-%m-%d")
            
            if "created_at" in user and user["created_at"]:
                user["created_at"] = user["created_at"].isoformat()
                
            if "updated_at" in user and user["updated_at"]:
                user["updated_at"] = user["updated_at"].isoformat()
            
            return {
                "success": True,
                "user": user
            }
    
    return {"success": False, "message": "User not found"}


def update_profile_service(email: str, profile_data: dict, image_url: str = None, image_public_id: str = None):
    """Update user profile by email"""
    collections_to_check = ["employee", "employer", "users"]
    user = None
    user_col = None
    
    # Find user
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        user = current_col.find_one({"email": email})
        if user:
            user_col = current_col
            break
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    new_email = profile_data.get("email")
    if new_email and new_email != email:
        email_check = check_email_uniqueness_for_update(new_email, exclude_user_id=str(user["_id"]))
        if email_check["exists"]:
            collection_names = {
                "users": "basic user account",
                "employee": "employee account", 
                "employer": "employer account"
            }
            existing_type = collection_names.get(email_check["collection"], "account")
            return {"success": False, "message": f"Email already exists in {existing_type}. Each email can only be used for one account type."}
    
    # Delete old image from Cloudinary if exists and new image is provided
    if image_url and image_public_id and user.get("image_public_id"):
        try:
            from src.utils.cloudinary import delete_image
            delete_image(user["image_public_id"])
        except Exception as e:
            print(f"[ERROR] Failed to delete old image: {e}")
    
    update_data = {
        "updated_at": datetime.now()
    }
    
    if "fullname" in profile_data:
        update_data["fullname"] = profile_data["fullname"]
    if "nickname" in profile_data:
        update_data["nickname"] = profile_data["nickname"]
    if "date_of_birth" in profile_data:
        if isinstance(profile_data["date_of_birth"], str):
            from datetime import datetime as dt
            date_formats = [
                "%d_%m_%Y",  
                "%Y_%m_%d",
                "%d-%m-%Y", 
                "%Y-%m-%d",  
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = dt.strptime(profile_data["date_of_birth"], fmt).date()
                    update_data["date_of_birth"] = datetime.combine(parsed_date, datetime.min.time())
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                return {"success": False, "message": f"Invalid date format: {profile_data['date_of_birth']}. Expected DD_MM_YYYY, YYYY_MM_DD, DD-MM-YYYY, or YYYY-MM-DD"}
        else:
            update_data["date_of_birth"] = profile_data["date_of_birth"]
    if "phone" in profile_data:
        update_data["phone"] = profile_data["phone"]
    if "gender" in profile_data:
        update_data["gender"] = profile_data["gender"]
    if "email" in profile_data:
        update_data["email"] = profile_data["email"]
    
    required_fields = ["fullname", "nickname", "date_of_birth", "phone", "gender"]
    if all(field in update_data for field in required_fields):
        update_data["is_profile_completed"] = True
    
    if image_url and image_public_id:
        update_data["image"] = image_url
        update_data["image_public_id"] = image_public_id
    
    # Update in database - use original email for the query, but update with new email if changed
    query_email = email 
    result = user_col.update_one(
        {"email": query_email}, 
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        return {"success": False, "message": "No changes made to profile"}
    
    new_email = profile_data.get("email", email)
    updated_user = user_col.find_one({"email": new_email}) or user_col.find_one({"email": query_email})
    
    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])
        updated_user.pop("password", None)
        
        # Convert datetime to string for JSON serialization
        if "date_of_birth" in updated_user and updated_user["date_of_birth"]:
            updated_user["date_of_birth"] = updated_user["date_of_birth"].strftime("%Y-%m-%d")
        
        if "created_at" in updated_user and updated_user["created_at"]:
            updated_user["created_at"] = updated_user["created_at"].isoformat()
            
        if "updated_at" in updated_user and updated_user["updated_at"]:
            updated_user["updated_at"] = updated_user["updated_at"].isoformat()
        
        return {"success": True, "user": updated_user}
    
    return {"success": False, "message": "Failed to retrieve updated profile"}


def delete_profile_service(email: str):
    """Delete user profile by email (soft delete)"""
    collections_to_check = ["employee", "employer", "users"]
    user = None
    user_col = None
    
    # Find user
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        user = current_col.find_one({"email": email})
        if user:
            user_col = current_col
            break
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    if user.get("image_public_id"):
        try:
            from src.utils.cloudinary import delete_image
            delete_image(user["image_public_id"])
        except Exception as e:
            print(f"[ERROR] Failed to delete image: {e}")
    
    result = user_col.delete_one(
        {"email": email}
    )
    
    if result.deleted_count > 0:
        return {"success": True, "message": "Profile permanently deleted successfully"}
    
    return {"success": False, "message": "Failed to delete profile"}
