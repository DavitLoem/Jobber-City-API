import uuid
from datetime import datetime, timezone, date
from bson import ObjectId
from fastapi import HTTPException, status

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.schema.sub_schema import EducationRequest
from src.domains.profile.seeker_profile.services.core_profile_service import calculate_completion_percentage

async def _update_completion_percentage(user_oid: ObjectId):
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    if profile:
        new_percentage = calculate_completion_percentage(profile)
        await seeker_profiles_collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {"profile_completion_percentage": new_percentage}}
        )

async def add_education(user_id: str, data: EducationRequest) -> dict:
    user_oid = ObjectId(user_id)
    edu_dict = data.model_dump()
    edu_dict["id"] = str(uuid.uuid4())
    
    if isinstance(edu_dict.get("start_date"), date):
        edu_dict["start_date"] = datetime.combine(edu_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(edu_dict.get("end_date"), date):
        edu_dict["end_date"] = datetime.combine(edu_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$push": {"educations": edu_dict}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found. Please update your core profile information first before adding education details.")

    await _update_completion_percentage(user_oid)
    return edu_dict

async def update_education(user_id: str, edu_id: str, data: EducationRequest) -> dict:
    user_oid = ObjectId(user_id)
    edu_dict = data.model_dump(exclude_unset=True)
    
    if not edu_dict:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    if isinstance(edu_dict.get("start_date"), date):
        edu_dict["start_date"] = datetime.combine(edu_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(edu_dict.get("end_date"), date):
        edu_dict["end_date"] = datetime.combine(edu_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    set_query = {f"educations.$.{k}": v for k, v in edu_dict.items()}

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid, "educations.id": edu_id},
        {"$set": set_query}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Education not found. Please check the education ID and try again.")

    await _update_completion_percentage(user_oid)
    edu_dict["id"] = edu_id
    return edu_dict

async def delete_education(user_id: str, edu_id: str) -> bool:
    user_oid = ObjectId(user_id)
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$pull": {"educations": {"id": edu_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Education not found. Please check the education ID and try again.")

    await _update_completion_percentage(user_oid)
    return True