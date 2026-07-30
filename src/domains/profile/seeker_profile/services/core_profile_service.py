from bson import ObjectId
from datetime import datetime, timezone, date

from fastapi import HTTPException

from src.core.mongo import seeker_profiles_collection, users_collection
from src.domains.profile.seeker_profile.models.seeker_profile_model import SeekerProfileModel
from src.domains.profile.seeker_profile.schema.core_schema import SeekerCoreProfileUpdateRequest

# ==========================================
# 📍 Helper Functions (មុខងារជំនួយ)
# ==========================================
def helper_format_profile(profile: dict) -> dict:
    """បំប្លែង _id ទៅជា id និង ObjectIds ផ្សេងទៀតទៅជា String សម្រាប់ Pydantic"""
    if not profile:
        return None
    
    # 🎯 ជួសជុល: ប្រើ .pop("_id", ObjectId()) ការពារ Error ពេលអត់មាន _id
    profile["id"] = str(profile.pop("_id", ObjectId()))
    
    profile["user_id"] = str(profile["user_id"])
    
    if profile.get("date_of_birth") and isinstance(profile["date_of_birth"], datetime):
        profile["date_of_birth"] = profile["date_of_birth"].strftime("%Y-%m-%d")
    
    if profile.get("province_id"):
        profile["province_id"] = str(profile["province_id"])
    if profile.get("district_id"):
        profile["district_id"] = str(profile["district_id"])
    
    # បំប្លែង Category IDs ពី ObjectId ទៅ String វិញ
    if "expertise_category_ids" in profile:
        profile["expertise_category_ids"] = [str(cid) for cid in profile["expertise_category_ids"]]
        
    return profile

def calculate_completion_percentage(profile: dict) -> int:
    """គណនាភាគរយនៃការបំពេញ Profile (ឧទាហរណ៍សាមញ្ញ)"""
    score = 0
    # ១. ព័ត៌មានផ្ទាល់ខ្លួនមូលដ្ឋាន (30%)
    if profile.get("first_name") and profile.get("last_name"): score += 10
    if profile.get("phone_number") or profile.get("email"): score += 10
    if profile.get("province_id"): score += 10
    
    # ២. ព័ត៌មានការងារ និងជំនាញ (40%)
    if profile.get("current_position"): score += 10
    if profile.get("skills") and len(profile["skills"]) > 0: score += 15
    if profile.get("biography"): score += 15
    
    # ៣. រូបថត និងឯកសារយោង (30%)
    if profile.get("profile_image_url"): score += 10
    if profile.get("resume_url"): score += 20
    
    return min(score, 100)  # ការពារកុំឱ្យលើស 100%

# ==========================================
# 📍 Core Profile Services
# ==========================================

async def get_seeker_profile(user_id: str) -> dict:
    """ទាញយក Profile របស់ Seeker តាមរយៈ user_id (បានមកពី Token)"""
    
    user_oid = ObjectId(user_id)
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    
    user_account = await users_collection.find_one({"_id": user_oid})
    if not user_account:
        raise HTTPException(status_code=404, detail="User account not found")
    
    user_info = {
        "first_name": user_account.get("first_name", ""),
        "last_name": user_account.get("last_name", ""),
        "email": user_account.get("email", "")
    }
    
    if not profile:
        empty_profile = SeekerProfileModel(user_id=user_id).to_create_dict()
        merged_profile = {**empty_profile, **user_info}
        
        return helper_format_profile(merged_profile)

    merged_profile = {**profile, **user_info}
    return helper_format_profile(merged_profile)

async def update_core_profile(user_id: str, data: SeekerCoreProfileUpdateRequest) -> dict:
    """Update ព័ត៌មានគោលដោយបែងចែកការ Save ទៅកាន់ Tables ពីរដាច់ពីគ្នា"""
    
    user_oid = ObjectId(user_id)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return await get_seeker_profile(user_id)

    now = datetime.now(timezone.utc)

    # 🎯 ជំហានទី ១: ញែកទិន្នន័យ និង Update ទៅកាន់ `users_collection`
    
    user_update_payload = {}
    
    # ប្រើ pop() ដើម្បីទាញយកផង និងលុបចេញពី update_data ផងកុំឱ្យវាសល់ទៅចូល profile
    if "first_name" in update_data:
        user_update_payload["first_name"] = update_data.pop("first_name")
    if "last_name" in update_data:
        user_update_payload["last_name"] = update_data.pop("last_name")
    if "email" in update_data:
        user_update_payload["email"] = update_data.pop("email")

    if user_update_payload:
        user_update_payload["updated_at"] = now
        await users_collection.update_one(
            {"_id": user_oid},
            {"$set": user_update_payload}
        )

    # ប្រសិនបើមានតែការ Update ឈ្មោះ/Email តែគ្មានអ្វីផ្សេងទៀត
    if not update_data:
        return await get_seeker_profile(user_id)

    # 🎯 ជំហានទី ២: បន្តការរៀបចំទិន្នន័យសម្រាប់ `seeker_profiles_collection`
    update_data["onboarding_completed"] = True
    update_data["updated_at"] = now

    if "date_of_birth" in update_data and isinstance(update_data["date_of_birth"], date):
        dt = update_data["date_of_birth"]
        update_data["date_of_birth"] = datetime.combine(dt, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    if "expertise_category_ids" in update_data:
        valid_ids = []
        for cid in update_data["expertise_category_ids"]:
            if not ObjectId.is_valid(cid):
                raise HTTPException(status_code=400, detail=f"Category ID '{cid}' is not valid")
            valid_ids.append(ObjectId(cid))
        update_data["expertise_category_ids"] = valid_ids

    if update_data.get("province_id"):
        if not ObjectId.is_valid(update_data["province_id"]):
            raise HTTPException(status_code=400, detail="Province ID is not valid")
        update_data["province_id"] = ObjectId(update_data["province_id"])

    if update_data.get("district_id"):
        if not ObjectId.is_valid(update_data["district_id"]):
            raise HTTPException(status_code=400, detail="District ID is not valid")
        update_data["district_id"] = ObjectId(update_data["district_id"])

    # ឆែកមើលថាតើគាត់មាន Profile ហើយឬនៅ
    existing_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})

    if existing_profile:
        # Update Profile ដែលមានស្រាប់
        merged_profile = {**existing_profile, **update_data}
        update_data["profile_completion_percentage"] = calculate_completion_percentage(merged_profile)
        
        await seeker_profiles_collection.update_one(
            {"user_id": user_oid},
            {"$set": update_data}
        )
    else:
        # បង្កើត Profile ថ្មី (ពេលនេះមិនត្រូវការ first_name និង last_name ក្នុង Model ទៀតទេ)
        new_profile_model = SeekerProfileModel(
            user_id=user_oid,
            **update_data
        )
        new_profile_dict = new_profile_model.to_create_dict()
        new_profile_dict["profile_completion_percentage"] = calculate_completion_percentage(new_profile_dict)
        
        await seeker_profiles_collection.insert_one(new_profile_dict)

    # ត្រឡប់ទិន្នន័យដោយហៅពី get_seeker_profile ដើម្បីប្រាកដថាបានទិន្នន័យពេញលេញ (មានឈ្មោះ និង Email)
    return await get_seeker_profile(user_id)