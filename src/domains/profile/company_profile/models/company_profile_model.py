from datetime import datetime, timezone
from bson import ObjectId

class CompanyProfileModel:
    def __init__(self, user_id: str | ObjectId, company_name: str, industry_id: str | ObjectId, 
                 company_size: str, description: str, contact_email: str, contact_phone: str, 
                 province_id: str | ObjectId, address_detail: str, 
                 district_id: str | ObjectId = None,
                 website_url: str = None, logo_url: str = None, banner_url: str = None,
                 is_verified: bool = True, status: str = "active"):
        
        # បំប្លែង String ID ទៅជា ObjectId
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.industry_id = ObjectId(industry_id) if isinstance(industry_id, str) else industry_id
        self.province_id = ObjectId(province_id) if isinstance(province_id, str) else province_id
        self.district_id = ObjectId(district_id) if isinstance(district_id, str) and district_id else district_id
        
        self.company_name = company_name
        self.company_size = company_size
        self.description = description
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.website_url = website_url
        self.address_detail = address_detail
        self.logo_url = logo_url
        self.banner_url = banner_url
        self.is_verified = is_verified
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
        # លុប Field ណាដែលជា None ចេញ ដើម្បីកុំឱ្យជាន់ទិន្នន័យចាស់ក្នុង DB (លើកលែងតែយើងចង់ Clear)
        filtered_data = {k: v for k, v in data.items() if v is not None}
        filtered_data["updated_at"] = datetime.now(timezone.utc)
        # មិនអនុញ្ញាតឱ្យ Update user_id ទេ
        filtered_data.pop("user_id", None)
        return filtered_data