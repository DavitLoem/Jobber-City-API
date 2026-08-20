from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional, Dict, Any

class SeekerProfileModel:
    def __init__(
        self, 
        user_id: str | ObjectId, 
        **kwargs
    ):
        # 🎯 ព័ត៌មានគោលដំបូង (តម្រូវឱ្យមាន)
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

        # 🎯 រូបភាព និងភាគរយ
        self.image_url = kwargs.get("image_url")
        self.profile_completion_percentage = kwargs.get("profile_completion_percentage", 0)
        self.onboarding_completed = kwargs.get("onboarding_completed", False)

        # 🎯 ព័ត៌មានផ្ទាល់ខ្លួន
        self.date_of_birth = kwargs.get("date_of_birth")
        self.gender = kwargs.get("gender")
        self.marital_status = kwargs.get("marital_status")
        self.nationality = kwargs.get("nationality")
        self.phone_number = kwargs.get("phone_number")
        self.current_position = kwargs.get("current_position")

        # 🎯 ទីតាំង
        prov_id = kwargs.get("province_id")
        self.province_id = ObjectId(prov_id) if prov_id else None
        
        dist_id = kwargs.get("district_id")
        self.district_id = ObjectId(dist_id) if dist_id else None
        
        
        add_prov_id = kwargs.get("address_province_id")
        self.address_province_id = ObjectId(add_prov_id) if add_prov_id else None
        add_dist_id = kwargs.get("address_district_id")
        self.address_district_id = ObjectId(add_dist_id) if add_dist_id else None
        self.commune = kwargs.get("commune")
        self.village = kwargs.get("village")
        self.street = kwargs.get("street")
        self.house_no = kwargs.get("house_no")

        # 🎯 ចំណង់ចំណូលចិត្តការងារ និង Biography
        self.biography = kwargs.get("biography")
        self.expected_salary_min = kwargs.get("expected_salary_min")
        self.expected_salary_max = kwargs.get("expected_salary_max")
        self.job_type_preferences = kwargs.get("job_type_preferences", [])
        
        # បំប្លែង Category IDs ទៅជា ObjectId ទាំងអស់
        cat_ids = kwargs.get("expertise_category_ids", [])
        self.expertise_category_ids = [ObjectId(cid) for cid in cat_ids if cid]
        
        self.skills = kwargs.get("skills", [])

        # 🎯 តំណភ្ជាប់ និងឯកសារ
        self.resume_url = kwargs.get("resume_url")
        self.resume_filename = kwargs.get("resume_filename") 
        self.resume_public_id = kwargs.get("resume_public_id") 
        self.portfolio_url = kwargs.get("portfolio_url")
        self.linkedin_url = kwargs.get("linkedin_url")

        # 🎯 ការពារ Error MongoDB: កំណត់ Array ទទេរជានិច្ច សម្រាប់ Sub-documents
        self.experiences = kwargs.get("experiences", [])
        self.educations = kwargs.get("educations", [])
        self.trainings = kwargs.get("trainings", [])
        self.languages = kwargs.get("languages", [])

    def to_create_dict(self) -> dict:
        """វេចខ្ចប់ទិន្នន័យសម្រាប់ Insert ចូល Database ដំបូង"""
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    # ចំណាំ: យើងមិនមាន to_update_dict ធំមួយទេ ព្រោះនៅក្នុង Profile យើងនឹង Update ជាផ្នែកៗ 
    # (ឧ. Update តែ Personal Info ឬ Update តែ Experiences) ដោយប្រើប្រាស់ Pydantic Schema និង $set ជំនួសវិញ។