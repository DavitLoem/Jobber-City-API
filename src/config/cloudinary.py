import os
import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

# Load Cloudinary configuration from environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image(file, folder="jobber_city"):
    """
    Upload an image to Cloudinary
    
    Args:
        file: File object or path to upload
        folder: Cloudinary folder to store the image
        
    Returns:
        dict: Contains secure_url, public_id, etc.
    """
    try:
        result = upload(
            file,
            folder=folder,
            resource_type="auto",
            allowed_formats=["jpg", "jpeg", "png", "gif", "webp"]
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

def delete_image(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: The public ID of the image to delete
        
    Returns:
        dict: Result of deletion
    """
    try:
        from cloudinary.api import delete_resources
        result = delete_resources([public_id], resource_type="image", type="upload")
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
