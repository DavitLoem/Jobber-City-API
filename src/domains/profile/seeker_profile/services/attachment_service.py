import uuid

from fastapi import UploadFile, HTTPException, status
from bson import ObjectId
from datetime import datetime, timezone

from src.core.mongo import seeker_profiles_collection
from src.domains.profile.seeker_profile.services.ai_service import analyze_cv_with_gemini
from src.utils.cloudinary import upload_document, upload_image
from src.domains.profile.seeker_profile.services.core_profile_service import (
    helper_format_profile,
    calculate_completion_percentage,
    ensure_seeker_profile_exists,
)
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
    # ធានាថា Profile មានស្រាប់ជាមុនសិន (បង្កើតទទេស្វ័យប្រវត្តិបើមិនទាន់មាន) រួចទាញយកមកគណនាភាគរយ
    await ensure_seeker_profile_exists(user_oid)
    existing_profile = await seeker_profiles_collection.find_one({"user_id": user_oid})

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

async def upload_and_parse_cv(user_id: str, file: UploadFile) -> dict:
    """
    ដំណើរការ៖ ឆែកឯកសារ ➔ អានអត្ថបទ ➔ ឱ្យ AI វិភាគ ➔ Upload ➔ Auto-Fill ចូល Database
    """
    user_oid = ObjectId(user_id)
    
    # ១. ត្រួតពិនិត្យប្រភេទ និងទំហំឯកសារ
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 5 * 1024 * 1024: # កំណត់ត្រឹម 5MB
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

    # ៥. Upload ឯកសារពិតទៅ Cloudinary
    upload_res = upload_document(file.file, folder="jobber_city/resumes")
    if not upload_res.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to Upload CV: {upload_res.get('message')}")

    resume_url = upload_res.get("url")

    # ៦. Smart Data Merging (បញ្ចូលទិន្នន័យទៅក្នុង Profile)
    # ធានាថា Profile មានស្រាប់ជាមុនសិន (Seeker អាច Upload CV ជាជំហានទីមួយបានផងដែរ)
    await ensure_seeker_profile_exists(user_oid)
    profile = await seeker_profiles_collection.find_one({"user_id": user_oid})

    extracted_data = ai_result.get("extracted_data", {})
    
    # ៦.១ កំណត់អថេរសម្រាប់ Update ធម្មតា
    update_fields = {
        "resume_url": resume_url,
        "updated_at": datetime.now(timezone.utc)
    }

    # ៦.២ បញ្ចូលជំនាញ (Skills) ដោយការពារកុំឱ្យស្ទួនគ្នា
    current_skills = profile.get("skills", [])
    new_skills = extracted_data.get("skills", [])
    if new_skills:
        combined_skills = list(set(current_skills + new_skills)) # set() ជួយលុបពាក្យស្ទួនអូតូ
        update_fields["skills"] = combined_skills

    # ៦.៣ រៀបចំកញ្ចប់សម្រាប់ $push Experiences និង Educations
    push_fields = {}

    def parse_ai_date(date_str):
        """បំប្លែងថ្ងៃខែដែល AI បោះមក ទៅជា Datetime របស់ MongoDB"""
        if not date_str: return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    # បញ្ចូល Experiences
    new_exps = extracted_data.get("experiences", [])
    if new_exps:
        formatted_exps = []
        for exp in new_exps:
            exp["id"] = str(uuid.uuid4()) # បង្កើត ID ឱ្យធាតុនីមួយៗ
            exp["start_date"] = parse_ai_date(exp.get("start_date"))
            exp["end_date"] = parse_ai_date(exp.get("end_date"))
            formatted_exps.append(exp)
        # ប្រើ $each ដើម្បីញាត់ Array ចូលក្នុង Array
        push_fields["experiences"] = {"$each": formatted_exps} 

    # បញ្ចូល Educations
    new_edus = extracted_data.get("educations", [])
    if new_edus:
        formatted_edus = []
        for edu in new_edus:
            edu["id"] = str(uuid.uuid4())
            edu["start_date"] = parse_ai_date(edu.get("start_date"))
            edu["end_date"] = parse_ai_date(edu.get("end_date"))
            formatted_edus.append(edu)
        push_fields["educations"] = {"$each": formatted_edus}

    # ៧. បញ្ជូនចូល Database
    update_query = {"$set": update_fields}
    if push_fields:
        update_query["$push"] = push_fields

    updated_profile = await seeker_profiles_collection.find_one_and_update(
        {"user_id": user_oid},
        update_query,
        return_document=True
    )

    # ៨. គណនាភាគរយ Profile សាជាថ្មី
    final_percentage = calculate_completion_percentage(updated_profile)
    updated_profile = await seeker_profiles_collection.find_one_and_update(
        {"user_id": user_oid},
        {"$set": {"profile_completion_percentage": final_percentage}},
        return_document=True
    )

    return helper_format_profile(updated_profile)