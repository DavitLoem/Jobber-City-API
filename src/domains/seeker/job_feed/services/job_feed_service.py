from bson import ObjectId
from src.core.mongo import job_posts_collection, districts_collection, provinces_collection, company_profiles_collection, employment_types_collection, work_types_collection, seeker_profiles_collection, job_applications_collection

class JobFeedService:
    
    def _format_feed_response(self, job_doc: dict) -> dict:
        """បំប្លែងទិន្នន័យដែលបាន Join រួច ទៅជាទម្រង់ JobFeedResponse"""
        district_name = job_doc.get("district", {}).get("name_en", "")
        province_name = job_doc.get("province", {}).get("name_en", "")
        
        if district_name and province_name:
            location = f"{district_name}, {province_name}"
        elif province_name:
            location = province_name
        else:
            location = "Unknown Location"
            
        return {
            "id": str(job_doc["_id"]), 
            "title": job_doc.get("title", ""), 
            "min_salary": job_doc.get("min_salary", 0), 
            "max_salary": job_doc.get("max_salary", 0), 
            "salary_period": job_doc.get("salary_period", ""), 
            "description": job_doc.get("description", []),
            "requirements": job_doc.get("requirements", []),
            "benefits": job_doc.get("benefits", []),
            "experience": job_doc.get("experience", ""),
            "working_days": job_doc.get("working_days", ""),
            "working_hours": job_doc.get("working_hours", ""),
            "is_negotiable": job_doc.get("is_negotiable", True),
            "headcount": job_doc.get("headcount", 1),
            "closing_date": job_doc.get("closing_date"),
            "company_name": job_doc.get("company", {}).get("company_name", "Unknown Company"), 
            "logo_url": job_doc.get("company", {}).get("logo_url"), 
            "location": location, 
            "employment_type": job_doc.get("employment_type", {}).get("name", "N/A"), 
            "work_type": job_doc.get("work_type", {}).get("name", "N/A"), 
            "created_at": job_doc.get("created_at"), 
            "is_saved": False, 
            "is_applied": job_doc.get("is_applied", False),
            "match_percentage": int(job_doc.get("match_percentage", 0))
        }

    # 🎯 ១. Function គណនាទម្ងន់ពិន្ទុ
    def _get_dynamic_weights(self, seeker_skills: list) -> dict:
        """កំណត់ទម្ងន់ពិន្ទុផ្អែកលើការបំពេញ Profile របស់អ្នកប្រើប្រាស់"""
        if not seeker_skills:
            return {"category": 60, "province": 20, "district": 20, "skill": 0}
        return {"category": 30, "province": 10, "district": 10, "skill": 50}

    # 🎯 ២. Function រៀបចំលក្ខខណ្ឌ (Filter & Sort)
    def _build_query_conditions(self, feed_type: str, category_id: str, seeker_profile: dict) -> tuple:
        """បង្កើតលក្ខខណ្ឌ $match និង $sort ទៅតាមប្រភេទ Feed"""
        seeker_categories = seeker_profile.get("expertise_category_ids", []) if seeker_profile else []
        seeker_province = seeker_profile.get("province_id") if seeker_profile else None
        
        if feed_type == "recommended":
            sort_stage = {"$sort": {"match_percentage": -1, "created_at": -1}}
            or_conditions = []
            if seeker_categories:
                or_conditions.append({"category_id": {"$in": seeker_categories}})
            if seeker_province:
                or_conditions.append({"province_id": ObjectId(seeker_province) if ObjectId.is_valid(seeker_province) else seeker_province})
            
            match_condition = {"status": "active", "$or": or_conditions} if or_conditions else {"status": "active"}
        else: # recent
            sort_stage = {"$sort": {"created_at": -1}}
            match_condition = {"status": "active"}
            if category_id and ObjectId.is_valid(category_id):
                match_condition["category_id"] = ObjectId(category_id)
                
        return match_condition, sort_stage

    # 🎯 ៣. Function បង្កើត Aggregation Pipeline ទាំងមូល
    def _build_pipeline(self, user_oid: ObjectId, skip: int, limit: int, match_condition: dict, sort_stage: dict, seeker_profile: dict, weights: dict) -> list:
        """ផ្គុំ Pipeline សម្រាប់បញ្ជូនទៅកាន់ MongoDB"""
        seeker_skills = seeker_profile.get("skills", []) if seeker_profile else []
        seeker_categories = seeker_profile.get("expertise_category_ids", []) if seeker_profile else []
        seeker_province = seeker_profile.get("province_id") if seeker_profile else None
        seeker_district = seeker_profile.get("district_id") if seeker_profile else None

        pipeline = [
            {"$match": match_condition},
            
            # --- THE MATCHING ENGINE ---
            {"$addFields": {
                "matched_skills_count": {"$size": { "$setIntersection": [ {"$ifNull": ["$required_skills", []]}, seeker_skills ] }},
                "total_skills_count": {"$size": { "$ifNull": ["$required_skills", []] }},
                "is_category_match": {"$in": ["$category_id", seeker_categories]},
                "is_province_match": {"$eq": ["$province_id", ObjectId(seeker_province) if seeker_province and ObjectId.is_valid(seeker_province) else None]},
                "is_district_match": {"$eq": ["$district_id", ObjectId(seeker_district) if seeker_district and ObjectId.is_valid(seeker_district) else None]}
            }},
            {"$addFields": {
                "skill_score": {"$cond": [{"$gt": ["$total_skills_count", 0]}, {"$multiply": [{"$divide": ["$matched_skills_count", "$total_skills_count"]}, weights["skill"]]}, 0]},
                "category_score": {"$cond": ["$is_category_match", weights["category"], 0]},
                "location_score": {"$add": [
                    {"$cond": ["$is_province_match", weights["province"], 0]},
                    {"$cond": ["$is_district_match", weights["district"], 0]}
                ]}
            }},
            {"$addFields": {"match_percentage": {"$round": [{"$add": ["$skill_score", "$category_score", "$location_score"]}, 0]}}},
            
            sort_stage,
            {"$skip": skip},
            {"$limit": limit},
            
            # --- THE LOOKUPS ---
            {"$lookup": {"from": company_profiles_collection.name, "localField": "company_id", "foreignField": "_id", "as": "company"}},
            {"$unwind": {"path": "$company", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {"from": provinces_collection.name, "localField": "province_id", "foreignField": "_id", "as": "province"}},
            {"$unwind": {"path": "$province", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {"from": districts_collection.name, "localField": "district_id", "foreignField": "_id", "as": "district"}},
            {"$unwind": {"path": "$district", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {"from": employment_types_collection.name, "localField": "employment_type_id", "foreignField": "_id", "as": "employment_type"}},
            {"$unwind": {"path": "$employment_type", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {"from": work_types_collection.name, "localField": "work_type_id", "foreignField": "_id", "as": "work_type"}},
            {"$unwind": {"path": "$work_type", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {
                "from": job_applications_collection.name,
                "let": {"jobId": "$_id", "seekerId": user_oid},
                "pipeline": [{"$match": {"$expr": {"$and": [{"$eq": ["$job_id", "$$jobId"]}, {"$eq": ["$seeker_user_id", "$$seekerId"]}]}}}],
                "as": "user_application"
            }},
            {"$addFields": {"is_applied": {"$gt": [{"$size": "$user_application"}, 0]}}}
        ]
        return pipeline

    # 🚀 Main Function ឥឡូវនេះខ្លី និងងាយស្រួលយល់
    async def get_jobs(self, user_id: str, feed_type: str = "recent", page: int = 1, limit: int = 10, category_id: str = None) -> list:
        """ទាញយកការងារចុងក្រោយបំផុត (Recent Jobs) និងការងារណែនាំ (Recommended)"""
        skip = (page - 1) * limit
        user_oid = ObjectId(user_id)
        
        # ទាញយក Profile 
        seeker_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
        seeker_skills = seeker_profile.get("skills", []) if seeker_profile else []
        
        # ១. ទាញយកការកំណត់ទម្ងន់ពិន្ទុ
        weights = self._get_dynamic_weights(seeker_skills)
        
        # ២. ទាញយកលក្ខខណ្ឌ Filter និង Sort
        match_condition, sort_stage = self._build_query_conditions(feed_type, category_id, seeker_profile)
        
        # ៣. ផ្គុំ Pipeline
        pipeline = self._build_pipeline(user_oid, skip, limit, match_condition, sort_stage, seeker_profile, weights)

        # ៤. បាញ់ទៅកាន់ Database និង Return លទ្ធផល
        cursor = job_posts_collection.aggregate(pipeline)
        
        job_feeds = []
        async for job in cursor:
            job_feeds.append(self._format_feed_response(job))
            
        return job_feeds
    
    async def search_jobs(self, user_id: str, keyword: str, page: int = 1, limit: int = 10) -> list:
        """ស្វែងរកការងារតាមរយៈពាក្យគន្លឹះ (Title, Skills ឬ Company Name)"""
        skip = (page - 1) * limit
        user_oid = ObjectId(user_id)
        
        # ១. ស្វែងរកក្រុមហ៊ុនដែលមានឈ្មោះពាក់ព័ន្ធនឹង Keyword ជាមុនសិន
        # ដើម្បីយក ID របស់ពួកគេទៅឆែកជាមួយ Job Posts
        matching_companies = await company_profiles_collection.find(
            {"company_name": {"$regex": keyword, "$options": "i"}}, 
            {"_id": 1}
        ).to_list(None)
        company_ids = [comp["_id"] for comp in matching_companies]

        # ២. កំណត់លក្ខខណ្ឌស្វែងរក (Search Condition)
        # $regex ជាមួយ option "i" មានន័យថា Case-insensitive (មិនប្រកាន់អក្សរតូចធំ)
        match_condition = {
            "status": "active",
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"required_skills": {"$regex": keyword, "$options": "i"}},
                {"company_id": {"$in": company_ids}}
            ]
        }
        
        # តម្រៀបតាមការងារដែលទើបបង្ហោះថ្មីៗ
        sort_stage = {"$sort": {"created_at": -1}}

        # ៣. ទាញយក Profile របស់អ្នកប្រើប្រាស់ដើម្បីគណនា Match Percentage
        seeker_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
        seeker_skills = seeker_profile.get("skills", []) if seeker_profile else []
        weights = self._get_dynamic_weights(seeker_skills)

        # ៤. ប្រើប្រាស់ Pipeline ដែលមានស្រាប់ដើម្បី Join និងគណនាពិន្ទុ
        pipeline = self._build_pipeline(
            user_oid=user_oid, 
            skip=skip, 
            limit=limit, 
            match_condition=match_condition, 
            sort_stage=sort_stage, 
            seeker_profile=seeker_profile, 
            weights=weights
        )

        # ៥. បាញ់ទៅកាន់ Database និង Return លទ្ធផល
        cursor = job_posts_collection.aggregate(pipeline)
        
        search_results = []
        async for job in cursor:
            search_results.append(self._format_feed_response(job))
            
        return search_results