import uuid
from bson import ObjectId
from fastapi import HTTPException, status

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.schema.sub_schema import LanguageRequest
from src.domains.profile.seeker_profile.services.core_profile_service import (
    calculate_completion_percentage,
    ensure_seeker_profile_exists,
)

async def _update_completion_percentage(user_oid: ObjectId):
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    if profile:
        new_percentage = calculate_completion_percentage(profile)
        await seeker_profiles_collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {"profile_completion_percentage": new_percentage}}
        )

async def add_language(user_id: str, data: LanguageRequest) -> dict:
    user_oid = ObjectId(user_id)
    lang_dict = data.model_dump()
    lang_dict["id"] = str(uuid.uuid4())

    await ensure_seeker_profile_exists(user_oid)

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$push": {"languages": lang_dict}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found. Please update your core profile information first before adding language details.")

    await _update_completion_percentage(user_oid)
    return lang_dict

async def update_language(user_id: str, lang_id: str, data: LanguageRequest) -> dict:
    user_oid = ObjectId(user_id)
    lang_dict = data.model_dump(exclude_unset=True)
    
    if not lang_dict:
        raise HTTPException(status_code=400, detail="No data provided for update.")

    set_query = {f"languages.$.{k}": v for k, v in lang_dict.items()}

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid, "languages.id": lang_id},
        {"$set": set_query}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Language not found.")

    await _update_completion_percentage(user_oid)
    lang_dict["id"] = lang_id
    return lang_dict

async def delete_language(user_id: str, lang_id: str) -> bool:
    user_oid = ObjectId(user_id)
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$pull": {"languages": {"id": lang_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Language not found.")

    await _update_completion_percentage(user_oid)
    return True