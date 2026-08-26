from bson import ObjectId
from typing import Optional
from datetime import datetime, timezone
from src.core.mongo import (
    users_collection, 
    seeker_profiles_collection, 
    job_applications_collection
)
from fastapi import HTTPException, status

class AdminSeekerService:

    # 🟢 ១. ទាញយកទិន្នន័យសម្រាប់ KPI Cards
    async def get_seeker_kpis(self) -> dict:
        import asyncio
        
        # រាប់តែ User ដែលមាន role = "seeker"
        base_query = {"role": "seeker"}
        
        t_total = users_collection.count_documents(base_query)
        t_active = users_collection.count_documents({**base_query, "is_active": True, "deleted_at": None})
        t_suspended = users_collection.count_documents({**base_query, "is_active": False, "deleted_at": None})
        t_banned = users_collection.count_documents({**base_query, "deleted_at": {"$ne": None}})
        
        total, active, suspended, banned = await asyncio.gather(t_total, t_active, t_suspended, t_banned)
        
        return {
            "total_seekers": total,
            "active": active,
            "suspended": suspended,
            "banned": banned
        }

    # 🟢 ២. ទាញយកបញ្ជី Job Seekers សម្រាប់តារាង
    async def get_seeker_list(self, search: Optional[str] = None, status_filter: Optional[str] = None, page: int = 1, limit: int = 10) -> dict:
        skip = (page - 1) * limit
        
        # កំណត់លក្ខខណ្ឌ Filter
        match_query = {"role": "seeker"}
        
        if status_filter == "active":
            match_query["is_active"] = True
            match_query["deleted_at"] = None
        elif status_filter == "suspended":
            match_query["is_active"] = False
            match_query["deleted_at"] = None
        elif status_filter == "banned":
            match_query["deleted_at"] = {"$ne": None}
            
        if search:
            # ស្វែងរកតាមឈ្មោះ ឬ អ៊ីមែល
            match_query["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
            
        pipeline = [
            {"$match": match_query},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            
            # 🔗 Join ទី ១៖ ទាញយកព័ត៌មាន Profile (លេខទូរស័ព្ទ, តួនាទី)
            {
                "$lookup": {
                    "from": seeker_profiles_collection.name,
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "profile_info"
                }
            },
            {"$unwind": {"path": "$profile_info", "preserveNullAndEmptyArrays": True}},
            
            # 🔗 Join ទី ២៖ រាប់ចំនួន Applications ដែលគាត់បានដាក់
            {
                "$lookup": {
                    "from": job_applications_collection.name,
                    "localField": "_id",
                    "foreignField": "seeker_user_id",
                    "as": "applications"
                }
            },
            # ប្រើ $addFields ដើម្បីរាប់ប្រវែង Array នៃ Applications
            {
                "$addFields": {
                    "applications_count": {"$size": {"$ifNull": ["$applications", []]}}
                }
            },
            # លុប array applications ចោលវិញដើម្បីកុំឱ្យទិន្នន័យធំពេក
            {"$project": {"applications": 0}} 
        ]
        
        cursor = users_collection.aggregate(pipeline)
        results = []
        
        async for user in cursor:
            profile = user.get("profile_info", {})
            
            # កំណត់ស្ថានភាព (Status) សម្រាប់បង្ហាញលើ UI
            is_active = user.get("is_active", True)
            deleted_at = user.get("deleted_at")
            
            user_status = "active"
            if deleted_at:
                user_status = "banned"
            elif not is_active:
                user_status = "suspended"
                
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            
            results.append({
                "user_id": str(user["_id"]),
                "full_name": f"{first_name} {last_name}".strip() or "Unknown",
                "avatar_url": user.get("avatar_url") or profile.get("image_url"),
                "current_position": profile.get("current_position", "Job Seeker"),
                "email": user.get("email", "N/A"),
                "phone_number": profile.get("phone_number", "N/A"),
                "applications_count": user.get("applications_count", 0),
                "status": user_status,
                "created_at": user.get("created_at")
            })
            
        total_count = await users_collection.count_documents(match_query)
        
        return {
            "items": results,
            "total": total_count,
            "page": page,
            "limit": limit
        }

    # 🟢 ៣. មុខងារ Suspend, Ban ឬ Activate គណនី
    async def update_seeker_status(self, user_id: str, action: str) -> dict:
        try:
            user_oid = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ទម្រង់ User ID មិនត្រឹមត្រូវទេ")

        now = datetime.now(timezone.utc)
        
        if action == "activate":
            update_data = {"is_active": True, "deleted_at": None, "updated_at": now}
        elif action == "suspend":
            update_data = {"is_active": False, "deleted_at": None, "updated_at": now}
        elif action == "ban":
            update_data = {"is_active": False, "deleted_at": now, "updated_at": now} # Soft Delete
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="សកម្មភាពមិនត្រឹមត្រូវ")

        result = await users_collection.update_one(
            {"_id": user_oid, "role": "seeker"},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="រកមិនឃើញគណនី Job Seeker នេះទេ")

        return {
            "user_id": user_id,
            "action": action
        }