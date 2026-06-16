import uuid
from datetime import datetime, timezone, date
from bson import ObjectId
from fastapi import HTTPException, status

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.schema.sub_schema import TrainingRequest
from src.domains.profile.seeker_profile.services.core_profile_service import calculate_completion_percentage


async def _update_completion_percentage(user_oid: ObjectId):
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    if profile:
        new_percentage = calculate_completion_percentage(profile)
        await seeker_profiles_collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {"profile_completion_percentage": new_percentage}}
        )

async def add_training(user_id: str, data: TrainingRequest) -> dict:
    user_oid = ObjectId(user_id)
    train_dict = data.model_dump()
    train_dict["id"] = str(uuid.uuid4())
    
    if isinstance(train_dict.get("start_date"), date):
        train_dict["start_date"] = datetime.combine(train_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(train_dict.get("end_date"), date):
        train_dict["end_date"] = datetime.combine(train_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$push": {"trainings": train_dict}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found. Please update your core profile information first before adding training details.")

    await _update_completion_percentage(user_oid)
    return train_dict

async def update_training(user_id: str, train_id: str, data: TrainingRequest) -> dict:
    user_oid = ObjectId(user_id)
    train_dict = data.model_dump(exclude_unset=True)
    
    if not train_dict:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    if isinstance(train_dict.get("start_date"), date):
        train_dict["start_date"] = datetime.combine(train_dict["start_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
    if isinstance(train_dict.get("end_date"), date):
        train_dict["end_date"] = datetime.combine(train_dict["end_date"], datetime.min.time()).replace(tzinfo=timezone.utc)

    set_query = {f"trainings.$.{k}": v for k, v in train_dict.items()}

    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid, "trainings.id": train_id},
        {"$set": set_query}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Training not found. Please check the training ID and try again.")

    await _update_completion_percentage(user_oid)
    train_dict["id"] = train_id
    return train_dict

async def delete_training(user_id: str, train_id: str) -> bool:
    user_oid = ObjectId(user_id)
    result = await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$pull": {"trainings": {"id": train_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Training not found. Please check the training ID and try again.")

    await _update_completion_percentage(user_oid)
    return True