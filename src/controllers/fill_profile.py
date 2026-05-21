
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from src.model.fill_profile import FillProfile
from src.services.fill_profile import fill_profile_service, get_profile_service, update_profile_service, delete_profile_service
from src.config.cloudinary import upload_image, delete_image

router = APIRouter(prefix="/api", tags=["Fill Profile"])


@router.post("/fill-profile", summary="Fill user profile")
async def fill_profile(
    image: Optional[UploadFile] = File(None, description="Optional new image"),
    fullname: str = Form(...),
    nickname: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    gender: str = Form(...)
):
    try:
        image_url = None
        image_public_id = None
        
        if image:
            image_result = upload_image(image.file)
            
            if not image_result["success"]:
                raise HTTPException(status_code=400, detail=f"Image upload failed: {image_result.get('message')}")
            
            image_url = image_result["url"]
            image_public_id = image_result["public_id"]
        
  
        from datetime import datetime
        

        date_formats = [
            "%d_%m_%Y",  
            "%Y_%m_%d",  
            "%d-%m-%Y",
            "%Y-%m-%d",
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_of_birth, fmt).date()
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {date_of_birth}. Expected DD_MM_YYYY, YYYY_MM_DD, DD-MM-YYYY, or YYYY-MM-DD")
        
        profile_data = FillProfile(
            fullname=fullname,
            nickname=nickname,
            date_of_birth=parsed_date,
            email=email,
            phone=phone,
            gender=gender
        )
        
        result = fill_profile_service(profile_data, image_url, image_public_id)
        

        if not result.get("success"):
            if image_public_id:
                delete_image(image_public_id)
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to update profile"))
        
        return {
            "status": "success",
            "message": "Profile updated successfully", 
            "data": result.get("user"),
            "image_url": image_url
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in fill_profile: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
  
  
@router.get("/profile", summary="Get user profile")
async def get_profile(email: str):
    """Get user profile by email"""
    try:
        result = get_profile_service(email)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "Profile not found"))
        
        return {
            "status": "success",
            "data": result.get("user")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put("/profile", summary="Update user profile")
async def update_profile(
    image: Optional[UploadFile] = File(None, description="Optional new image"),
    fullname: Optional[str] = Form(None),
    nickname: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    email: str = Form(...),
    new_email: Optional[str] = Form(None, description="Optional new email address"),
    phone: Optional[str] = Form(None),
    gender: Optional[str] = Form(None)
):
    """Update user profile (partial update - only provided fields will be updated)"""
    try:
        image_url = None
        image_public_id = None
        
        if image:
            image_result = upload_image(image.file)
            
            if not image_result["success"]:
                raise HTTPException(status_code=400, detail=f"Image upload failed: {image_result.get('message')}")
            
            image_url = image_result["url"]
            image_public_id = image_result["public_id"]
        

        profile_data = {}
        
        if fullname is not None:
            profile_data["fullname"] = fullname
        if nickname is not None:
            profile_data["nickname"] = nickname
        if date_of_birth is not None:
         
            from datetime import datetime
            date_formats = [
                "%d_%m_%Y",
                "%Y_%m_%d",  
                "%d-%m-%Y", 
                "%Y-%m-%d",  
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_of_birth, fmt).date()
                    profile_data["date_of_birth"] = date_of_birth
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                raise HTTPException(status_code=400, detail=f"Invalid date format: {date_of_birth}. Expected DD_MM_YYYY, YYYY_MM_DD, DD-MM-YYYY, or YYYY-MM-DD")
        
        if phone is not None:
            profile_data["phone"] = phone
        if gender is not None:
            profile_data["gender"] = gender
        if new_email is not None:
            profile_data["email"] = new_email
        
        result = update_profile_service(email, profile_data, image_url, image_public_id)
        

        if not result.get("success"):
            if image_public_id:
                delete_image(image_public_id)
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to update profile"))
        
    
        return {
            "status": "success",
            "message": "Profile updated successfully", 
            "data": result.get("user"),
            "image_url": image_url
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in update_profile: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/profile", summary="Delete user profile")
async def delete_profile(email: str):
    """Delete user profile by email (soft delete)"""
    try:
        result = delete_profile_service(email)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "Profile not found"))
        
        return {
            "status": "success",
            "message": result.get("message")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in delete_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
