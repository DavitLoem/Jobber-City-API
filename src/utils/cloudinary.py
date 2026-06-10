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
            allowed_formats=["jpg", "jpeg", "png", "webp"] # ដក gif ចេញប្រសិនបើមិនចង់ឱ្យ Seeker ដាក់រូប Profile ចលនា
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