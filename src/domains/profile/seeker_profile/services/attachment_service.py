import uuid

from fastapi import UploadFile, HTTPException, status
from bson import ObjectId
from datetime import datetime, timezone

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.services.ai_service import analyze_cv_with_gemini
from src.utils.cloudinary import upload_document, upload_image
from src.domains.profile.seeker_profile.services.core_profile_service import helper_format_profile, calculate_completion_percentage
from src.utils.pdf_extractor import extract_text_from_pdf

async def upload_profile_image(user_id: str, file: UploadFile) -> dict:
    """មុខងារសម្រាប់ Upload រូបថត Profile ទៅកាន់ Cloudinary និង Update ចូល Database"""
    
    # ១. ត្រួតពិនិត្យប្រភេទឯកសារ (Validation)
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Only image files are allowed!"
        )
        
    # ២. ត្រួតពិនិត្យទំហំឯកសារ (ឧទាហរណ៍ កំណត់ត្រឹម 5MB)
    file.file.seek(0, 2) # ប្រើបច្ចេកទេស Seek រំកិលទៅចុងឯកសារ ដើម្បីអានទំហំ (Bytes)
    file_size = file.file.tell() 
    file.file.seek(0) # 🎯 សំខាន់បំផុត! ត្រូវរំកិលមកដើម (0) វិញ ទើប Cloudinary អាច Upload ចេញ
    
    # កំណត់ទំហំអតិបរមា 5MB (5 * 1024 * 1024 bytes)
    MAX_FILE_SIZE = 5 * 1024 * 1024 
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, # លេខកូដ 413 គឺសម្រាប់បញ្ហា File ធំពេក
            detail="Image size too large! Please upload an image smaller than 5MB."
        )

    # ៣. ធ្វើការ Upload ទៅ Cloudinary (ប្រើ Cloudinary Utility ដែលយើងបានរៀបចំ)
    upload_result = upload_image(file.file, folder="jobber_city/profiles")
    
    if not upload_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to upload image: {upload_result.get('message')}"
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
            detail="Please update your profile information first before uploading a profile image."
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

async def process_and_extract_cv(user_id: str, file: UploadFile) -> dict:
    """
    ដំណើរការ៖ ឆែកឯកសារ ➔ អានអត្ថបទ ➔ ឱ្យ AI វិភាគ ➔ Upload បើពិតជា CV ➔ បោះ JSON ឱ្យ Frontend (មិន Save ទេ)
    """
    user_oid = ObjectId(user_id)
    
    # ១. ត្រួតពិនិត្យប្រភេទ និងទំហំឯកសារ
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 5 * 1024 * 1024: 
        raise HTTPException(status_code=413, detail="File too large! Please upload a file smaller than 5MB.")

    # ២. ទាញយកអត្ថបទពី PDF
    extracted_text = await extract_text_from_pdf(file)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Cannot extract text from the uploaded PDF. Please ensure it's a valid CV.")

    # ៣. ឱ្យ Gemini វិភាគ និងទាញយកទិន្នន័យ
    ai_result = await analyze_cv_with_gemini(extracted_text)

    # ៤. ការសម្រេចចិត្ត (Decision)
    if not ai_result.get("is_cv", False):
        reason = ai_result.get("reason", "The uploaded file is not a valid CV.")
        raise HTTPException(status_code=400, detail=f"The file has been rejected: {reason}")

    # ៥. Upload ឯកសារពិតទៅ Cloudinary ព្រោះ AI បញ្ជាក់ថាវាជា CV មែន
    upload_res = upload_document(file.file, folder="jobber_city/resumes")
    if not upload_res.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to Upload CV: {upload_res.get('message')}")

    resume_url = upload_res.get("url")

    # ៦. ធ្វើការរក្សាទុកតែ resume_url ប៉ុណ្ណោះ
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
    if not profile:
        raise HTTPException(status_code=404, detail="Please update your profile information first.")

    updated_profile = await seeker_profiles_collection.find_one_and_update(
        {"user_id": user_oid},
        {"$set": {
            "resume_url": resume_url,
            "updated_at": datetime.now(timezone.utc)
        }},
        return_document=True
    )
    
    # គណនាភាគរយ Profile សាជាថ្មី ព្រោះមានការ Update resume_url
    final_percentage = calculate_completion_percentage(updated_profile)
    await seeker_profiles_collection.update_one(
        {"user_id": user_oid},
        {"$set": {"profile_completion_percentage": final_percentage}}
    )

    # ៧. រៀបចំទិន្នន័យសម្រាប់បោះទៅ Frontend
    extracted_data = ai_result.get("extracted_data", {})
    
    # 💡 Logic ថ្មី៖ លុប personal_info ចេញ បើគាត់ធ្លាប់មានលេខទូរស័ព្ទ ឬ អ៊ីមែលរួចហើយក្នុង DB
    # (យើងសន្មតថាបើរូបគាត់មាន phone ឬ email មានន័យថាគាត់បំពេញ Profile រួចហើយ)
    if profile.get("phone_number") or profile.get("email"):
        extracted_data.pop("personal_info", None)

    return {
        "resume_url": resume_url,
        "parsed_data": extracted_data # បោះទិន្នន័យនេះទៅឱ្យ Frontend ប្រើ
    }