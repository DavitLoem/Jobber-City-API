from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

# 🎯 Import Database Collections 
from src.core.mongo import users_collection, company_profiles_collection, industries_collection, provinces_collection, districts_collection

# 🎯 Import Models & Schemas
from src.domains.profile.company_profile.models.company_profile_model import CompanyProfileModel
from src.domains.profile.company_profile.schemas.company_profile_schema import CompanyProfileCreate, CompanyProfileUpdate


class CompanyProfileService:
    
    def _format_response(self, profile: dict) -> dict:
        """បំប្លែងទិន្នន័យពី MongoDB ទៅជាទម្រង់ Response Schema ឱ្យបានស្អាត"""
        if not profile: return None
        return {
            "id": str(profile["_id"]),
            "user_id": str(profile["user_id"]),
            "company_name": profile.get("company_name", ""),
            "industry_id": str(profile.get("industry_id", "")),
            "company_size": profile.get("company_size", ""),
            "description": profile.get("description", ""),
            "contact_email": profile.get("contact_email", ""),
            "contact_phone": profile.get("contact_phone", ""),
            "website_url": profile.get("website_url"),
            "province_id": str(profile.get("province_id", "")),
            "district_id": str(profile.get("district_id", "")) if profile.get("district_id") else None,
            "address_detail": profile.get("address_detail", ""),
            "logo_url": profile.get("logo_url"),
            "banner_url": profile.get("banner_url"),
            "is_verified": profile.get("is_verified", True),
            "status": profile.get("status", "active")
        }

    async def _verify_master_data_exists(self, industry_id: str, province_id: str, district_id: str = None):
        """ឆែកមើលថា industry_id, province_id និង district_id ពិតជាមានមែនឬអត់ ព្រមទាំងឆែកទំនាក់ទំនងខេត្តនិងស្រុក"""
        
        # ១. ឆែក Industry (រក្សាដដែល)
        if industry_id:
            if not ObjectId.is_valid(industry_id):
                # dont write message khmer
                 raise HTTPException(status_code=400, detail="Industry ID is not valid.")
            industry = await industries_collection.find_one({"_id": ObjectId(industry_id)})
            if not industry:
                raise HTTPException(status_code=404, detail="Industry not found.")

        # ២. ឆែក ខេត្ត/ក្រុង (រក្សាដដែល)
        if province_id:
            if not ObjectId.is_valid(province_id):
                 raise HTTPException(status_code=400, detail="ID Province/City is not valid.")
            prov = await provinces_collection.find_one({"_id": ObjectId(province_id)})
            if not prov:
                raise HTTPException(status_code=404, detail="Province not found.")

        # ៣. ឆែក ស្រុក/ខណ្ឌ និង ទំនាក់ទំនងរបស់វាជាមួយខេត្ត
        if district_id:
            if not ObjectId.is_valid(district_id):
                 raise HTTPException(status_code=400, detail="ID District/Commune is not valid.")
            
            dist = await districts_collection.find_one({"_id": ObjectId(district_id)})
            if not dist:
                raise HTTPException(status_code=404, detail="District not found.")
            
            # 🎯 លក្ខខណ្ឌថ្មី: ផ្ទៀងផ្ទាត់ថា ស្រុកនេះ ពិតជាស្ថិតក្នុងខេត្តដែលបានរើសមែនឬអត់
            if str(dist.get("province_id")) != str(province_id):
                raise HTTPException(
                    status_code=400, 
                    detail="Data is not valid: The selected district/commune is not located in the chosen province/city."
                )


    async def get_my_company_profile(self, user_id: str) -> dict:
        """ទាញយកព័ត៌មានក្រុមហ៊ុនរបស់ Employer ផ្ទាល់"""
        profile = await company_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found.")
        return self._format_response(profile)


    async def create_company_profile(self, user_id: str, payload: CompanyProfileCreate) -> dict:
        """បង្កើតព័ត៌មានក្រុមហ៊ុនថ្មី (1 User = 1 Company)"""
        user_oid = ObjectId(user_id)

        # ឆែកមើលក្រែង Employer ម្នាក់នេះមាន Company រួចហើយ
        existing_profile = await company_profiles_collection.find_one({"user_id": user_oid})
        if existing_profile:
            raise HTTPException(status_code=400, detail="Your account already has a company profile.")

        # ឆែកសុពលភាព Master Data (Industry និង Location)
        await self._verify_master_data_exists(payload.industry_id, payload.province_id, payload.district_id)

        # ឆែកក្រែងឈ្មោះក្រុមហ៊ុននេះមានគេប្រើហើយ (ការពារកុំឱ្យជាន់ឈ្មោះគ្នា)
        existing_name = await company_profiles_collection.find_one({"company_name": {"$regex": f"^{payload.company_name}$", "$options": "i"}})
        if existing_name:
            raise HTTPException(status_code=400, detail=f"Company name '{payload.company_name}' is already taken.")

        # បំប្លែង Payload ទៅជា Model ដើម្បី Save ចូល DB
        new_model = CompanyProfileModel(
            user_id=user_oid,
            **payload.model_dump() # ស្រាយអថេរទាំងអស់ចេញពី Pydantic Schema
        )
        
        new_dict = new_model.to_create_dict()
        
        # Save ចូល Database
        await company_profiles_collection.insert_one(new_dict)
        
        # ប្តូរ role របស់ User ឱ្យទៅជា "employer_verified" ឬ "active_employer" 
        # នៅទីនេះយើងសន្មត់ថាគាត់ទើបតែមាន Profile ពេញលេញ
        await users_collection.update_one(
            {"_id": user_oid},
            {"$set": {"has_company_profile": True}} 
        )

        return self._format_response(new_dict)


    async def update_company_profile(self, user_id: str, payload: CompanyProfileUpdate) -> dict:
        """កែប្រែព័ត៌មានក្រុមហ៊ុន"""
        user_oid = ObjectId(user_id)
        
        # ឆែករកមើល Company
        profile = await company_profiles_collection.find_one({"user_id": user_oid})
        if not profile:
             raise HTTPException(status_code=404, detail="No company profile found to update.")

        # ឆែកសុពលភាព Master Data (ប្រសិនបើគាត់មានកែប្រែ)
        await self._verify_master_data_exists(payload.industry_id, payload.province_id, payload.district_id)

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update.")

        # ឆែកក្រែងឈ្មោះក្រុមហ៊ុនជាន់គេ (បើគាត់ចង់ប្តូរឈ្មោះ)
        if "company_name" in update_data:
            existing_name = await company_profiles_collection.find_one({
                "company_name": {"$regex": f"^{update_data['company_name']}$", "$options": "i"},
                "_id": {"$ne": profile["_id"]} # មិនរាប់បញ្ចូល Company ខ្លួនឯង
            })
            if existing_name:
                raise HTTPException(status_code=400, detail="This company name is already in use.")

        # បំប្លែងទិន្នន័យ និងបញ្ចូលថ្មី
        update_model = CompanyProfileModel(
            user_id=user_oid,
            industry_id=update_data.get("industry_id", str(profile["industry_id"])),
            province_id=update_data.get("province_id", str(profile["province_id"])),
            district_id=update_data.get("district_id", str(profile["district_id"])),
            company_name=update_data.get("company_name", profile["company_name"]),
            company_size=update_data.get("company_size", profile["company_size"]),
            description=update_data.get("description", profile["description"]),
            contact_email=update_data.get("contact_email", profile["contact_email"]),
            contact_phone=update_data.get("contact_phone", profile["contact_phone"]),
            address_detail=update_data.get("address_detail", profile["address_detail"])
        )
        
        update_dict = update_model.to_update_dict()
        
        # ដោយសារ `to_update_dict` អាចមានទិន្នន័យលើស យើងត្រូវរើសយកតែ Field ដែល User បញ្ជូនមក + updated_at
        final_update = {k: v for k, v in update_dict.items() if k in update_data or k == "updated_at"}

        updated_profile = await company_profiles_collection.find_one_and_update(
            {"_id": profile["_id"]},
            {"$set": final_update},
            return_document=True
        )

        return self._format_response(updated_profile)
    

    async def upload_logo(self, user_id: str, logo_url: str) -> dict:
        """Upload Link រូបភាព Logo របស់ក្រុមហ៊ុន"""
        user_oid = ObjectId(user_id)
        
        # upload to DB
        updated_profile = await company_profiles_collection.find_one_and_update(
            {"user_id": user_oid},
            {"$set": {"logo_url": logo_url}, "updated_at": datetime.now(timezone.utc)},
            return_document=True
        )
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Company profile not found.")

        return self._format_response(updated_profile)