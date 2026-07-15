from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

class JobPostModel:
    def __init__(self, company_id: str | ObjectId, title: str, description: List[str], 
                 requirements: List[str], benefits: List[str], min_salary: float, 
                 max_salary: float, salary_period: str, is_negotiable: bool, headcount: int,
                 experience: str, working_days: str, working_hours: str, 
                 category_id: str | ObjectId, job_level_id: str | ObjectId, 
                 work_type_id: str | ObjectId, employment_type_id: str | ObjectId, 
                 education_level_id: str | ObjectId, required_skills: List[str], customer_skills: List[str],
                 province_id: str | ObjectId, closing_date: datetime,
                 district_id: Optional[str | ObjectId] = None, 
                 specific_schedule: Optional[List[dict]] = None,
                 status: str = "active"):
        
        # បំប្លែង Foreign Keys ទាំងអស់ទៅជា ObjectId
        self.company_id = ObjectId(company_id) if isinstance(company_id, str) else company_id
        self.category_id = ObjectId(category_id) if isinstance(category_id, str) else category_id
        self.job_level_id = ObjectId(job_level_id) if isinstance(job_level_id, str) else job_level_id
        self.work_type_id = ObjectId(work_type_id) if isinstance(work_type_id, str) else work_type_id
        self.employment_type_id = ObjectId(employment_type_id) if isinstance(employment_type_id, str) else employment_type_id
        self.education_level_id = ObjectId(education_level_id) if isinstance(education_level_id, str) else education_level_id
        self.province_id = ObjectId(province_id) if isinstance(province_id, str) else province_id
        
        if district_id:
            self.district_id = ObjectId(district_id) if isinstance(district_id, str) else district_id
        else:
            self.district_id = None
            
        # បំប្លែង Array នៃ skill_ids
        self.required_skills = [ObjectId(skill) if isinstance(skill, str) else skill for skill in required_skills]
        self.customer_skills = customer_skills or []
        
        self.title = title
        self.description = description
        self.requirements = requirements
        self.benefits = benefits
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.salary_period = salary_period
        self.is_negotiable = is_negotiable
        self.headcount = headcount
        self.experience = experience
        self.working_days = working_days
        self.working_hours = working_hours
        self.specific_schedule = specific_schedule or []
        
        # ត្រូវប្រាកដថា closing_date មាន timezone
        self.closing_date = closing_date if closing_date.tzinfo else closing_date.replace(tzinfo=timezone.utc)
        self.status = status

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["_id"] = ObjectId()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    def to_update_dict(self) -> dict:
        data = self.__dict__.copy()
        # លុប Field ដែល None ចេញ ដើម្បីកុំឱ្យជាន់ទិន្នន័យចាស់
        filtered_data = {k: v for k, v in data.items() if v is not None}
        filtered_data["updated_at"] = datetime.now(timezone.utc)
        # មិនអនុញ្ញាតឱ្យកែប្រែ company_id ទេ
        filtered_data.pop("company_id", None)
        return filtered_data