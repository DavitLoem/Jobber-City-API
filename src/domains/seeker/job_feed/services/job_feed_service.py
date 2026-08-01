from bson import ObjectId
from src.core.mongo import job_posts_collection, districts_collection, provinces_collection, company_profiles_collection, employment_types_collection, work_types_collection, seeker_profiles_collection, job_applications_collection

class JobFeedService:
    
    def _format_feed_response(self, job_doc: dict) -> dict:
        """បំប្លែងទិន្នន័យដែលបាន Join រួច ទៅជាទម្រង់ JobFeedResponse"""
        
        # រៀបចំទីតាំង (ឧ. រុស្សីកែវ, ភ្នំពេញ) 
        district_name = job_doc.get("district", {}).get("name_en", "")
        province_name = job_doc.get("province", {}).get("name_en", "")
        
        if district_name and province_name:
            location = f"{district_name}, {province_name}"
        elif province_name:
            location = province_name
        else:
            location = "Unknown Location"
            
        match_score = job_doc.get("match_percentage", 0) 
            
        return {
            "id": str(job_doc["_id"]), 
            "title": job_doc.get("title", ""), 
            "min_salary": job_doc.get("min_salary", 0), 
            "max_salary": job_doc.get("max_salary", 0), 
            "salary_period": job_doc.get("salary_period", ""), 
            
            # 🎯 បន្ថែមទិន្នន័យ Detail ត្រង់នេះ (ទាញចេញពី Database)
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
            "match_percentage": int(match_score) 
        }

    async def get_jobs(self, user_id: str, feed_type: str = "recent", page: int = 1, limit: int = 10, category_id: str = None) -> list:
        """ទាញយកការងារចុងក្រោយបំផុត (Recent Jobs) ជាមួយមុខងារ Pagination"""
    
        skip = (page - 1) * limit
        user_oid = ObjectId(user_id)
        
        seeker_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
        seeker_skills = seeker_profile.get("skills", []) if seeker_profile else []
        seeker_categories = seeker_profile.get("expertise_category_ids", []) if seeker_profile else []
        
        if feed_type == "recommended":
            sort_stage = {"$sort": {"match_percentage": -1, "created_at": -1}}
        else: # លំនាំដើមគឺ "recent"
            sort_stage = {"$sort": {"created_at": -1}}
            
        match_condition = {"status": "active"}
        if category_id and ObjectId.is_valid(category_id):
            match_condition["category_id"] = ObjectId(category_id)
        
        pipeline = [
            # ១. ជ្រើសរើសយកតែការងារណាដែលកំពុង Active
            {"$match": match_condition},
            
            # 💡 --- THE MATCHING ENGINE --- 💡
            # ក. រកចំនួន Skills ដែលជាន់គ្នា និងឆែកមើល Category
            {"$addFields": {
                "matched_skills_count": {
                    "$size": { "$setIntersection": [ {"$ifNull": ["$required_skills", []]}, seeker_skills ] }
                },
                "total_skills_count": {
                    "$size": { "$ifNull": ["$required_skills", []] }
                },
                "is_category_match": {
                    "$in": ["$category_id", seeker_categories]
                }
            }},
            
            # ខ. គណនាពិន្ទុ (Category 30 + Skill 70)
            {"$addFields": {
                "skill_score": {
                    "$cond": [
                        {"$gt": ["$total_skills_count", 0]}, # បើក្រុមហ៊ុនមានដាក់ទាមទារ Skill
                        {"$multiply": [{"$divide": ["$matched_skills_count", "$total_skills_count"]}, 70]}, # (ជាន់គ្នា/សរុប) * 70
                        0 # បើក្រុមហ៊ុនអត់ទាមទារ Skill អីសោះ បាន 0 ពិន្ទុ (ឬអាចកែតាមចង់បាន)
                    ]
                },
                "category_score": {
                    "$cond": ["$is_category_match", 30, 0] # បើត្រូវ Category បាន 30 បើមិនត្រូវ បាន 0
                }
            }},
            
            # គ. បូកពិន្ទុបញ្ចូលគ្នា និងធ្វើឱ្យទៅជាចំនួនគត់ (Round)
            {"$addFields": {
                "match_percentage": {"$round": [{"$add": ["$skill_score", "$category_score"]}, 0]}
            }},
            
            # ២. រៀបតាមការប្រកាសថ្មីបំផុត
            sort_stage,
            
            # ៣. កំណត់ទំព័រ (Pagination)
            {"$skip": skip},
            {"$limit": limit},
            
            # ៤. តភ្ជាប់ជាមួយ Profile ក្រុមហ៊ុន
            {
                "$lookup": {
                    "from": company_profiles_collection.name,
                    "localField": "company_id",
                    "foreignField": "_id",
                    "as": "company"
                }
            },
            {"$unwind": {"path": "$company", "preserveNullAndEmptyArrays": True}},
            
            # ៥. តភ្ជាប់ជាមួយខេត្ត/ក្រុង
            {
                "$lookup": {
                    "from": provinces_collection.name,
                    "localField": "province_id",
                    "foreignField": "_id",
                    "as": "province"
                }
            },
            {"$unwind": {"path": "$province", "preserveNullAndEmptyArrays": True}},
            
            # ៦. តភ្ជាប់ជាមួយស្រុក/ខណ្ឌ
            {
                "$lookup": {
                    "from": districts_collection.name,
                    "localField": "district_id",
                    "foreignField": "_id",
                    "as": "district"
                }
            },
            {"$unwind": {"path": "$district", "preserveNullAndEmptyArrays": True}},
            
            # ៧. តភ្ជាប់ជាមួយ Employment Type (Full Time, Part Time...)
            {
                "$lookup": {
                    "from": employment_types_collection.name,
                    "localField": "employment_type_id",
                    "foreignField": "_id",
                    "as": "employment_type"
                }
            },
            {"$unwind": {"path": "$employment_type", "preserveNullAndEmptyArrays": True}},
            
            # ៨. តភ្ជាប់ជាមួយ Work Type (Remote, On-site...)
            {
                "$lookup": {
                    "from": work_types_collection.name,
                    "localField": "work_type_id",
                    "foreignField": "_id",
                    "as": "work_type"
                }
            },
            {"$unwind": {"path": "$work_type", "preserveNullAndEmptyArrays": True}},
            # 9. តភ្ជាប់ជាមួយ Job Applications
            {
                "$lookup": {
                    "from": job_applications_collection.name,
                    "let": {"jobId": "$_id", "seekerId": user_oid},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$job_id", "$$jobId"]},
                                    {"$eq": ["$seeker_user_id", "$$seekerId"]}
                                ]
                            }
                        }}
                    ],
                    "as": "user_application"
                }
            },
            {"$addFields": {
                "is_applied": {"$gt": [{"$size": "$user_application"}, 0]}
            }}
        ]

        # បញ្ជាឱ្យ MongoDB ដំណើរការ Pipeline
        cursor = job_posts_collection.aggregate(pipeline)
        
        # បំប្លែងទិន្នន័យ (Format) ហើយបញ្ជូនត្រឡប់ទៅវិញ
        job_feeds = []
        async for job in cursor:
            job_feeds.append(self._format_feed_response(job))
            
        return job_feeds