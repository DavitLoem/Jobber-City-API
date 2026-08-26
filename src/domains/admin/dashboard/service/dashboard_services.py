# src/domains/admin/dashboard/service/dashboard_services.py
import asyncio
from typing import Dict
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import calendar
from src.core.mongo import (
    users_collection,
    job_posts_collection,
    job_applications_collection,
    categories_collection
)

async def get_dashboard_kpi_summary() -> Dict:
    # ១. រាប់ User សរុប (មិនទាន់លុប)
    task_total_users = users_collection.count_documents({"deleted_at": None})
    
    # 🎯 ២. រាប់ Employer ដែលអត់ទាន់បំពេញប្រវត្តិរូបក្រុមហ៊ុន (Incomplete Profiles)
    task_incomplete_profiles = users_collection.count_documents({
        "role": "employer",               
        "is_profile_completed": False,    
        "deleted_at": None                
    })
    
    # ៣. រាប់ការងារសកម្ម
    task_active_jobs = job_posts_collection.count_documents({
        "status": "active"
    })
    
    # ៤. រាប់ចំនួនពាក្យសុំការងារសរុប
    task_total_applications = job_applications_collection.count_documents({})

    # ដំណើរការព្រមគ្នា (Concurrent)
    total_users, incomplete_profiles, active_jobs, total_apps = await asyncio.gather(
        task_total_users,
        task_incomplete_profiles,
        task_active_jobs,
        task_total_applications
    )

    return {
        "total_users": {
            "value": total_users,
            "trend": 12.0, 
            "trend_label": "this month"
        },
        "pending_verifications": { # 🎯 ប្រើឈ្មោះ Key ថ្មី
            "value": incomplete_profiles,
            "trend": None, 
            "trend_label": "Needs follow-up" # ដូរពាក្យ Label
        },
        "active_jobs": {
            "value": active_jobs,
            "trend": 5.0, 
            "trend_label": "this week"
        },
        "total_applications": {
            "value": total_apps,
            "trend": -2.0, 
            "trend_label": "this week"
        }
    }
    
async def get_platform_growth(months: int = 6) -> dict:
    """គណនាកំណើនអ្នកប្រើប្រាស់ (Seeker vs Employer) ក្នុងរយៈពេល x ខែចុងក្រោយ"""
    
    # ១. កំណត់ថ្ងៃចាប់ផ្តើម (ឧ. ៦ ខែមុនគិតពីថ្ងៃនេះ)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - relativedelta(months=months - 1)
    # កំណត់ឱ្យចាប់ផ្តើមពីថ្ងៃទី ១ នៃខែនោះ ដើម្បីឱ្យក្រាហ្វចេញមកស្អាត
    start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ២. Aggregation Pipeline
    pipeline = [
        {"$match": {
            "created_at": {"$gte": start_date, "$lte": end_date},
            "deleted_at": None,
            "role": {"$in": ["seeker", "employer"]}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"},
                "role": "$role"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]

    cursor = users_collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # ៣. រៀបចំទិន្នន័យ (Format) សម្រាប់ Frontend
    # បង្កើត List ខែទទេ ដើម្បីធានាថាទោះខែណាអត់មានអ្នកចុះឈ្មោះ ក៏នៅតែមានខែនោះលើក្រាហ្វ
    categories = []
    seeker_data = []
    employer_data = []
    
    # បង្កើត Dictionary ដើម្បីងាយស្រួល Map ទិន្នន័យ
    data_map = {"seeker": {}, "employer": {}}
    
    for doc in results:
        year_month = f"{doc['_id']['year']}-{doc['_id']['month']:02d}"
        role = doc['_id']['role']
        data_map[role][year_month] = doc['count']

    # បញ្ចូលទិន្នន័យតាមខែនីមួយៗ
    current_date = start_date
    while current_date <= end_date:
        month_abbr = calendar.month_abbr[current_date.month] # ឧ. 'Jan', 'Feb'
        year_month = f"{current_date.year}-{current_date.month:02d}"
        
        categories.append(month_abbr)
        seeker_data.append(data_map["seeker"].get(year_month, 0))
        employer_data.append(data_map["employer"].get(year_month, 0))
        
        current_date += relativedelta(months=1)

    return {
        "categories": categories,
        "series": [
            {"name": "Job Seekers", "data": seeker_data},
            {"name": "Employers", "data": employer_data}
        ]
    }


async def get_jobs_by_category() -> dict:
    """រាប់ចំនួនការងារសកម្មតាមប្រភេទ (យកតែ ៤ ប្រភេទកំពូលៗ)"""
    
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$category_id",
            "count": {"$sum": 1}
        }},
        # Join ជាមួយ categories_collection ដើម្បីយកឈ្មោះ Category
        {"$lookup": {
            "from": "categories",
            "localField": "_id",
            "foreignField": "_id",
            "as": "category_info"
        }},
        {"$unwind": "$category_info"},
        {"$sort": {"count": -1}},
        {"$limit": 4} # យកតែ Top 4 ដើម្បីបង្ហាញលើ Donut Chart
    ]

    cursor = job_posts_collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    labels = []
    series = []
    total_active_jobs = await job_posts_collection.count_documents({"status": "active"})

    for doc in results:
        # បើឈ្មោះ Category ជា Object ដែលមាន multiple languages (ឧ. {"en": "Tech", "km": "បច្ចេកវិទ្យា"})
        # យើងចាប់យកឈ្មោះ English មកបង្ហាញ ឬចាប់យកវាផ្ទាល់បើវាជា String
        name = doc['category_info'].get('name', 'Unknown')
        if isinstance(name, dict):
            name = name.get('en', 'Unknown')
            
        labels.append(name)
        series.append(doc['count'])

    return {
        "labels": labels,
        "series": series,
        "total_active_jobs": total_active_jobs
    }