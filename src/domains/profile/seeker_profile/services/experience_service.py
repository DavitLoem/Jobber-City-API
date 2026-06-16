import uuid
from datetime import datetime, timezone, date
from bson import ObjectId
from fastapi import HTTPException, status

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.schema.sub_schema import ExperienceRequest
from src.domains.profile.seeker_profile.services.core_profile_service import calculate_completion_percentage


# ==========================================
# 📍 Helper Function សម្រាប់គណនាភាគរយឡើងវិញ
# ==========================================
async def _update_completion_percentage(user_oid: ObjectId):
    """រាល់ពេលមានការបន្ថែម លុប ឬកែប្រែបទពិសោធន៍ យើងត្រូវគណនាភាគរយ Profile ឡើងវិញ"""
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    if profile:
        new_percentage = calculate_completion_percentage(profile)
        await seeker_profiles_collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {"profile_completion_percentage": new_percentage}}
        )

# ==========================================
# 📍 Experience CRUD Services
# ==========================================

async def add_experience(user_id: str, data: ExperienceRequest) -> dict:
    """បញ្ជូលបទពិសោធន៍ថ្មី (ប្រើ $push)"""
    user_oid = ObjectId(user_id)
    
    # ១. វេចខ្ចប់ទិន្នន័យ និងបង្កើត ID ថ្មីមួយសម្រាប់ចំណាំបទពិសោធន៍នេះ
    exp_dict = data.model_dump()
    exp_dict["id"] = str(uuid.uuid4())
    
    # ២. បំប្លែងថ្ងៃខែពី date ទៅ datetime (ដូចដែលយើងធ្លាប់ជួសជុល Error ពីមុន)
    if isinstance(exp_dict.get("start_date"), date):
        exp_dict["start_date"] = datetime.combine(exp_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(exp_dict.get("end_date"), date):
        exp_dict["end_date"] = datetime.combine(exp_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    # ៣. ប្រើ $push ដើម្បីញាត់ចូលទៅក្នុង Array ឈ្មោះ "experiences"
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$push": {"experiences": exp_dict}}
    )

    # បើរកមិនឃើញ Profile ទេ មានន័យថាគាត់មិនទាន់ Update ព័ត៌មានគោលសោះ
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Profile not found. Please update your core profile information first before adding experiences."
        )

    # ៤. គណនាភាគរយឡើងវិញ
    await _update_completion_percentage(user_oid)

    return exp_dict


async def update_experience(user_id: str, exp_id: str, data: ExperienceRequest) -> dict:
    """កែប្រែបទពិសោធន៍ចាស់ (ប្រើ Positional Operator $)"""
    user_oid = ObjectId(user_id)
    
    exp_dict = data.model_dump(exclude_unset=True)
    if not exp_dict:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    if isinstance(exp_dict.get("start_date"), date):
        exp_dict["start_date"] = datetime.combine(exp_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(exp_dict.get("end_date"), date):
        exp_dict["end_date"] = datetime.combine(exp_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    # 🎯 ចំណុចសំខាន់: រៀបចំទម្រង់ update ឱ្យចំ Index របស់ Array 
    # ឧទាហរណ៍: {"experiences.$.job_title": "Senior Developer"}
    set_query = {}
    for key, value in exp_dict.items():
        set_query[f"experiences.$.{key}"] = value

    # ស្វែងរក Profile ដែលមាន user_id នេះ "ហើយ" ក្នុង Array នោះត្រូវមាន id ស្មើនឹង exp_id
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid, "experiences.id": exp_id},
        {"$set": set_query}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Experience not found. Please check the experience ID and try again.")

    await _update_completion_percentage(user_oid)
    
    exp_dict["id"] = exp_id
    return exp_dict


async def delete_experience(user_id: str, exp_id: str) -> bool:
    """លុបបទពិសោធន៍ចោល (ប្រើ $pull)"""
    user_oid = ObjectId(user_id)
    
    # ប្រើ $pull ដើម្បីទាញ Object ដែលមាន id ស្មើនឹង exp_id ចេញពី Array
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$pull": {"experiences": {"id": exp_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Experience not found. Please check the experience ID and try again.")

    await _update_completion_percentage(user_oid)
    
    return True