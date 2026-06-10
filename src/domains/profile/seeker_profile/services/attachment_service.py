from fastapi import UploadFile, HTTPException, status
from bson import ObjectId
from datetime import datetime, timezone

from src.core.mongo import seeker_profiles_collection
from src.utils.cloudinary import upload_image
from src.domains.profile.seeker_profile.services.core_profile_service import helper_format_profile, calculate_completion_percentage

async def upload_profile_image(user_id: str, file: UploadFile) -> dict:
    """មុខងារសម្រាប់ Upload រូបថត Profile ទៅកាន់ Cloudinary និង Update ចូល Database"""
    
    # ១. ត្រួតពិនិត្យប្រភេទឯកសារ (Validation)
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="ឯកសារដែលបានជ្រើសរើសមិនមែនជារូបភាពទេ។"
        )
        
    # ២. ត្រួតពិនិត្យទំហំឯកសារ (ឧទាហរណ៍ កំណត់ត្រឹម 5MB)
    # ចំណាំ: FastAPI ទាមទារឱ្យយើងអាន (read) file ទើបដឹងទំហំ 
    # តែយើងអាចទុកឱ្យ Cloudinary បដិសេធដោយខ្លួនឯងក៏បាន ដើម្បីកុំឱ្យស្មុគស្មាញកូដនៅទីនេះ។

    # ៣. ធ្វើការ Upload ទៅ Cloudinary (ប្រើ Cloudinary Utility ដែលយើងបានរៀបចំ)
    upload_result = upload_image(file.file, folder="jobber_city/profiles")
    
    if not upload_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"បរាជ័យក្នុងការ Upload រូបភាព: {upload_result.get('message')}"
        )

    new_image_url = upload_result.get("url")
    user_oid = ObjectId(user_id)

    # ៤. Update ចូល Database
    # ទាញយក Profile ចាស់សិន ដើម្បីគណនាភាគរយឡើងវិញ
    existing_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    
    if not existing_profile:
        # បើគាត់មិនទាន់មាន Profile ទេ (មិនទាន់ Update ព័ត៌មានគោលសោះ) មិនគួរឱ្យគាត់ Upload រូបមុនទេ
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="សូមកែប្រែព័ត៌មានផ្ទាល់ខ្លួនរបស់អ្នកជាមុនសិន មុននឹងបញ្ចូលរូបថត។"
        )

    # Update URL ថ្មី និងគណនាភាគរយ
    existing_profile["profile_image_url"] = new_image_url
    new_percentage = calculate_completion_percentage(existing_profile)

    updated_profile = await seeker_profiles_collection.find_one_and_update(
        {"user_id": user_oid},
        {"$set": {
            "profile_image_url": new_image_url,
            "profile_completion_percentage": new_percentage,
            "updated_at": datetime.now(timezone.utc)
        }},
        return_document=True
    )

    return helper_format_profile(updated_profile)

# CV Upload