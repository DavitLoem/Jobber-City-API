from bson import ObjectId
from typing import Dict, Any, Optional
from src.core.mongo import (
    company_profiles_collection, 
    users_collection, 
    industries_collection
)

class AdminCompanyService:

    # 🟢 ១. ទាញយកទិន្នន័យសម្រាប់ KPI Cards
    async def get_company_kpis(self) -> dict:
        """ទាញយកចំនួនក្រុមហ៊ុនសរុប និងតាមស្ថានភាព"""
        # ដោយផ្អែកលើ CompanyProfileModel យើងមាន field is_verified និង status[cite: 21]
        
        import asyncio
        t_total = company_profiles_collection.count_documents({"status": {"$ne": "deleted"}})
        t_pending = company_profiles_collection.count_documents({"is_verified": False, "status": "pending"})
        t_verified = company_profiles_collection.count_documents({"is_verified": True})
        t_rejected = company_profiles_collection.count_documents({"status": "rejected"})
        
        total, pending, verified, rejected = await asyncio.gather(t_total, t_pending, t_verified, t_rejected)
        
        return {
            "total_companies": total,
            "pending_approval": pending,
            "verified": verified,
            "rejected": rejected
        }

    # 🟢 ២. ទាញយកបញ្ជីក្រុមហ៊ុន (Aggregation)
    async def get_company_list(self, search: Optional[str] = None, status_filter: Optional[str] = None, page: int = 1, limit: int = 10) -> dict:
        """ទាញយកបញ្ជីក្រុមហ៊ុនសម្រាប់បង្ហាញក្នុងតារាង ដោយមានការ Join និង Filter"""
        skip = (page - 1) * limit
        
        # កំណត់លក្ខខណ្ឌ (Match Stage)
        match_query = {"status": {"$ne": "deleted"}}
        if status_filter:
            if status_filter == "pending":
                match_query["is_verified"] = False
                match_query["status"] = "pending"
            elif status_filter == "verified":
                match_query["is_verified"] = True
            elif status_filter == "rejected":
                match_query["status"] = "rejected"
                
        if search:
            # ស្វែងរកតាមឈ្មោះក្រុមហ៊ុន[cite: 21]
            match_query["company_name"] = {"$regex": search, "$options": "i"}
            
        pipeline = [
            {"$match": match_query},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            
            # 🔗 Join ទី ១៖ ទាញយកព័ត៌មានម្ចាស់គណនី (Owner) តាមរយៈ user_id[cite: 21]
            {
                "$lookup": {
                    "from": users_collection.name,
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "owner_info"
                }
            },
            {"$unwind": {"path": "$owner_info", "preserveNullAndEmptyArrays": True}},
            
            # 🔗 Join ទី ២៖ ទាញយកឈ្មោះ Industry តាមរយៈ industry_id[cite: 21]
            {
                "$lookup": {
                    "from": industries_collection.name,
                    "localField": "industry_id",
                    "foreignField": "_id",
                    "as": "industry_info"
                }
            },
            {"$unwind": {"path": "$industry_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor = company_profiles_collection.aggregate(pipeline)
        results = []
        
        async for comp in cursor:
            owner = comp.get("owner_info", {})
            industry = comp.get("industry_info", {})
            
            # យកនាមត្រកូល និងនាមខ្លួនមកភ្ជាប់គ្នាផ្អែកលើ User Model[cite: 19]
            first_name = owner.get("first_name", "")
            last_name = owner.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or "Unknown"
            
            results.append({
                "company_id": str(comp["_id"]),
                "company_name": comp.get("company_name", "Unknown"),
                "logo_url": comp.get("logo_url"),
                "province_id": str(comp.get("province_id")) if comp.get("province_id") else None,
                "industry_name": industry.get("name", "N/A"),
                "owner_name": full_name,
                "owner_email": owner.get("email", "N/A"), # យកអ៊ីមែលពី User Model[cite: 19]
                "status": comp.get("status", "pending"),
                "is_verified": comp.get("is_verified", False),
                "created_at": comp.get("created_at")
            })
            
        total_count = await company_profiles_collection.count_documents(match_query)
        
        return {
            "items": results,
            "total": total_count,
            "page": page,
            "limit": limit
        }