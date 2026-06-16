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
    
    if not profile:
        # 🎯 ទាញយកទិន្នន័យពី Table 'users' មកបំពេញអូតូ
        user_account = await users_collection.find_one({"_id": user_oid})
        
        first_name = ""
        last_name = ""
        email = ""
        phone = ""

        if user_account:
            # 🎯 ឥឡូវនេះយើងគ្រាន់តែទាញយក first_name និង last_name ត្រង់ៗតែម្តង
            first_name = user_account.get("first_name", "")
            last_name = user_account.get("last_name", "")
            email = user_account.get("email", "")
            phone = user_account.get("phone_number", "")
        
        # បង្កើតទម្រង់ទទេរ ដោយមានភ្ជាប់ទិន្នន័យពី Account មកស្រាប់
        empty_profile = SeekerProfileModel(
            user_id=user_id, 
            first_name=first_name, 
            last_name=last_name,
            email=email,
            phone_number=phone
        ).to_create_dict()
        
        return helper_format_profile(empty_profile)

    return helper_format_profile(profile)

async def update_core_profile(user_id: str, data: SeekerCoreProfileUpdateRequest) -> dict:
    """Update ព័ត៌មានគោលរបស់ Seeker (ប្រើ Upsert Logic)"""
    
    user_oid = ObjectId(user_id)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return await get_seeker_profile(user_id)

    # ==========================================
    # 🎯 ជួសជុល: ត្រួតពិនិត្យភាពត្រឹមត្រូវនៃ ObjectId មុននឹងបំប្លែង
    # ==========================================
    if "date_of_birth" in update_data and isinstance(update_data["date_of_birth"], date):
        dt = update_data["date_of_birth"]
        # បន្ថែមម៉ោង 00:00:00 ចូល ហើយកំណត់ម៉ោងជា UTC
        update_data["date_of_birth"] = datetime.combine(dt, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    if "expertise_category_ids" in update_data:
        valid_ids = []
        for cid in update_data["expertise_category_ids"]:
            if not ObjectId.is_valid(cid):
                raise HTTPException(status_code=400, detail=f"Category ID '{cid}' is not valid (must be a 24-character hex)")
            valid_ids.append(ObjectId(cid))
        update_data["expertise_category_ids"] = valid_ids

    if update_data.get("province_id"):
        if not ObjectId.is_valid(update_data["province_id"]):
            raise HTTPException(status_code=400, detail="Province ID is not valid (must be a 24-character hex)")
        update_data["province_id"] = ObjectId(update_data["province_id"])

    if update_data.get("district_id"):
        if not ObjectId.is_valid(update_data["district_id"]):
            raise HTTPException(status_code=400, detail="District ID is not valid (must be a 24-character hex)")
        update_data["district_id"] = ObjectId(update_data["district_id"])
    # ==========================================

    # ៣. អាប់ដេតម៉ោង
    update_data["updated_at"] = datetime.now(timezone.utc)

    # ៤. ឆែកមើលថាតើគាត់មាន Profile ហើយឬនៅ?
    existing_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})

    if existing_profile:
        # គណនាភាគរយថ្មី ដោយផ្អែកលើទិន្នន័យចាស់ បូកបញ្ជូលទិន្នន័យថ្មី
        merged_profile = {**existing_profile, **update_data}
        update_data["profile_completion_percentage"] = calculate_completion_percentage(merged_profile)
        
        # UPDATE
        updated_profile = await seeker_profiles_collection.find_one_and_update(
            {"user_id": user_oid},
            {"$set": update_data},
            return_document=True
        )
    else:
        # CREATE NEW (បើគាត់ទើបតែ Login ហើយចុច Update យកតែម្តង)
        
        # ១. ទាញ (pop) ឈ្មោះចេញពី update_data ដើម្បីកុំឱ្យជាន់គ្នាពេលប្រើ **update_data
        f_name = update_data.pop("first_name", "")
        l_name = update_data.pop("last_name", "")
        
        # ២. បើគាត់អត់បានបោះឈ្មោះមកទេ យើងទៅទាញពីគណនី (users) មកបំពេញឱ្យ
        if not f_name or not l_name:
            user_account = await users_collection.find_one({"_id": user_oid})
            if user_account:
                f_name = f_name or user_account.get("first_name", "")
                l_name = l_name or user_account.get("last_name", "")

        # ៣. បង្កើត Model (ពេលនេះលែងជាន់គ្នាទៀតហើយ)
        new_profile_model = SeekerProfileModel(
            user_id=user_oid,
            first_name=f_name,
            last_name=l_name,
            **update_data
        )
        
        new_profile_dict = new_profile_model.to_create_dict()
        new_profile_dict["profile_completion_percentage"] = calculate_completion_percentage(new_profile_dict)
        
        await seeker_profiles_collection.insert_one(new_profile_dict)
        updated_profile = new_profile_dict

    return helper_format_profile(updated_profile)