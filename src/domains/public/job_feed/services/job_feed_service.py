from bson import ObjectId
from src.core.mongo import job_posts_collection, districts_collection, provinces_collection, company_profiles_collection, employment_types_collection, work_types_collection

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
            location = "ទីតាំងមិនបានបញ្ជាក់"
            
        return {
            "id": str(job_doc["_id"]),
            "title": job_doc.get("title", ""),
            "min_salary": job_doc.get("min_salary", 0),
            "max_salary": job_doc.get("max_salary", 0),
            "salary_period": job_doc.get("salary_period", ""),
            "company_name": job_doc.get("company", {}).get("company_name", "Unknown Company"),
            "logo_url": job_doc.get("company", {}).get("logo_url"),
            "location": location,
            "employment_type": job_doc.get("employment_type", {}).get("name", "N/A"),
            "work_type": job_doc.get("work_type", {}).get("name", "N/A"),
            "created_at": job_doc.get("created_at"),
            "is_saved": False, # លំនាំដើមសិន ព្រោះ Public មិនទាន់ Login
            "match_percentage": None
        }

    async def get_recent_jobs(self, page: int = 1, limit: int = 10) -> list:
        """ទាញយកការងារចុងក្រោយបំផុត (Recent Jobs) ជាមួយមុខងារ Pagination"""
        
        # គណនាចំនួនដែលត្រូវរំលង (Skip) សម្រាប់ទំព័រនីមួយៗ
        skip = (page - 1) * limit
        
        pipeline = [
            # ១. ជ្រើសរើសយកតែការងារណាដែលកំពុង Active
            {"$match": {"status": "active"}},
            
            # ២. រៀបតាមការប្រកាសថ្មីបំផុត
            {"$sort": {"created_at": -1}},
            
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
            {"$unwind": {"path": "$work_type", "preserveNullAndEmptyArrays": True}}
        ]

        # បញ្ជាឱ្យ MongoDB ដំណើរការ Pipeline
        cursor = job_posts_collection.aggregate(pipeline)
        
        # បំប្លែងទិន្នន័យ (Format) ហើយបញ្ជូនត្រឡប់ទៅវិញ
        job_feeds = []
        async for job in cursor:
            job_feeds.append(self._format_feed_response(job))
            
        return job_feeds