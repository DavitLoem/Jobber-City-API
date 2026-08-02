import cloudinary
from cloudinary.uploader import upload, destroy
from src.core.config import settings  # 🎯 ទាញយក settings ពី config មកប្រើ

# 🎯 កំណត់ Configuration ដោយប្រើប្រាស់ Pydantic Settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_document(file, folder="jobber_city/resumes"):
    """
    មុខងារសម្រាប់ Upload ឯកសារ (PDF, DOCX) ទៅ Cloudinary
    """
    try:
        result = upload(
            file,
            folder=folder,
            resource_type="auto", # auto អនុញ្ញាតឱ្យ Cloudinary ស្គាល់ PDF ដោយស្វ័យប្រវត្តិ
            allowed_formats=["pdf", "doc", "docx"]
        )
        return {
            "success": True,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format")
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

def upload_image(file, folder: str = "jobber_city") -> dict:
    """
    Upload an image to Cloudinary
    
    Args:
        file: File object (FastAPI UploadFile.file) or file path
        folder: Cloudinary folder to store the image
        
    Returns:
        dict: Contains success status, url, public_id, etc.
    """
    try:
        result = upload(
            file,
            folder=folder,
            resource_type="auto",
            allowed_formats=["jpg", "jpeg", "png", "webp"]
        )
        return {
            "success": True,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "width": result.get("width"),
            "height": result.get("height")
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

def delete_image(public_id: str) -> dict:
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: The public ID of the image to delete
        
    Returns:
        dict: Result of deletion
    """
    try:
        # 🎯 ប្រើប្រាស់ destroy ជំនួសឱ្យ delete_resources សម្រាប់លុបឯកសារទោល
        result = destroy(public_id, resource_type="image")
        
        # Cloudinary នឹង return {"result": "ok"} ប្រសិនបើជោគជ័យ
        if result.get("result") == "ok":
            return {"success": True}
        else:
            return {"success": False, "message": result.get("result", "Unknown error")}
            
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
        
def delete_document(public_id: str) -> dict:
    """
    មុខងារសម្រាប់លុបឯកសារ PDF ចេញពី Cloudinary
    """
    try:
        # សាកល្បងលុបជាទម្រង់ image ជាមុន (ព្រោះ Cloudinary ច្រើនតែចាត់ទុក PDF ជា Image ដើម្បីបង្កើត Thumbnail)
        result = destroy(public_id, resource_type="image")
        if result.get("result") == "ok":
            return {"success": True}
            
        # ប្រសិនបើមិនជោគជ័យ សាកល្បងលុបជាទម្រង់ raw
        result_raw = destroy(public_id, resource_type="raw")
        if result_raw.get("result") == "ok":
            return {"success": True}
            
        return {"success": False, "message": result.get("result", "Unknown error")}
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }