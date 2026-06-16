from typing import Optional
from pydantic import BaseModel, Field, EmailStr

# ==========================================
# ផ្នែក REQUEST (សម្រាប់ Create)
# ==========================================
class CompanyProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150, description="ឈ្មោះក្រុមហ៊ុន")
    industry_id: str = Field(..., description="ID នៃប្រភេទអាជីវកម្ម (Master Data)")
    company_size: str = Field(..., description="ទំហំក្រុមហ៊ុន ឧ. '1-50 Employees'")
    description: str = Field(..., min_length=10, description="ការពិពណ៌នាអំពីក្រុមហ៊ុន")
    
    contact_email: EmailStr = Field(..., description="អ៊ីមែលសម្រាប់ទំនាក់ទំនងការងារ")
    contact_phone: str = Field(..., min_length=8, description="លេខទូរស័ព្ទទំនាក់ទំនង")
    website_url: Optional[str] = Field(None, description="គេហទំព័រក្រុមហ៊ុន (មិនកាតព្វកិច្ច)")
    
    province_id: str = Field(..., description="ID នៃខេត្ត/ក្រុង (ទាញពី job_provinces)")
    district_id: Optional[str] = Field(None, description="ID នៃស្រុក/ខណ្ឌ (មិនកាតព្វកិច្ច)")
    address_detail: str = Field(..., description="អាសយដ្ឋានផ្ទះ/ផ្លូវលម្អិត")
    
    # ចំណាំ៖ logo_url និង banner_url យើងអត់ទាមទារពេល Create ទេ 
    # ព្រោះ Employer ត្រូវប្រើ Route មួយផ្សេងទៀតដើម្បី Upload រូបភាព។

# ==========================================
# ផ្នែក REQUEST (សម្រាប់ Update)
# ==========================================
class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=150)
    industry_id: Optional[str] = Field(None)
    company_size: Optional[str] = Field(None)
    description: Optional[str] = Field(None, min_length=10)
    
    contact_email: Optional[EmailStr] = Field(None)
    contact_phone: Optional[str] = Field(None, min_length=8)
    website_url: Optional[str] = Field(None)
    
    province_id: Optional[str] = Field(None)
    district_id: Optional[str] = Field(None)
    address_detail: Optional[str] = Field(None)

# ==========================================
# ផ្នែក RESPONSE
# ==========================================
class CompanyProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    industry_id: str
    company_size: str
    description: str
    contact_email: str
    contact_phone: str
    website_url: Optional[str] = None
    province_id: str
    district_id: Optional[str] = None
    address_detail: str
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    is_verified: bool
    status: str