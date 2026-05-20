from datetime import datetime
from typing import List, Optional
from src.config.mongo import collections
from src.config.cloudinary import upload_image, delete_image
from src.model.slider import SliderRequest

def create_slider_service(slider_data: SliderRequest, image_file) -> dict:
    """Create a new slider with Cloudinary image upload"""
    try:
        # 1. Upload image to Cloudinary
        image_result = upload_image(image_file)
        
        if not image_result["success"]:
            return {
                "success": False,
                "message": f"Image upload failed: {image_result.get('message')}"
            }
        
        # 2. Prepare slider data
        slider_col = collections("sliders")
        slider_dict = slider_data.model_dump()
        slider_dict.update({
            "image_url": image_result["url"],
            "image_public_id": image_result["public_id"],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        # 3. Insert into database
        result = slider_col.insert_one(slider_dict)
        
        return {
            "success": True,
            "slider_id": str(result.inserted_id),
            "message": "Slider created successfully",
            "image_url": image_result["url"]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create slider: {str(e)}"
        }

def get_all_sliders_service() -> dict:
    """Get all active sliders ordered by order field"""
    try:
        slider_col = collections("sliders")
        
        # Find active sliders and sort by order
        sliders = list(slider_col.find(
            {"is_active": True},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("order", 1))
        
        return {
            "success": True,
            "data": sliders,
            "count": len(sliders)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get sliders: {str(e)}",
            "data": [],
            "count": 0
        }

def get_slider_by_id_service(slider_id: str) -> dict:
    """Get a specific slider by ID"""
    try:
        from bson import ObjectId
        
        slider_col = collections("sliders")
        slider = slider_col.find_one({"_id": ObjectId(slider_id)})
        
        if slider:
            # Convert ObjectId to string and exclude it from response
            slider["_id"] = str(slider["_id"])
            return {
                "success": True,
                "data": slider
            }
        else:
            return {
                "success": False,
                "message": "Slider not found"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get slider: {str(e)}"
        }

def update_slider_service(slider_id: str, slider_data: SliderRequest, image_file=None) -> dict:
    """Update an existing slider with optional image update"""
    try:
        from bson import ObjectId
        
        slider_col = collections("sliders")
        
        # Get current slider to handle image replacement
        current_slider = slider_col.find_one({"_id": ObjectId(slider_id)})
        if not current_slider:
            return {
                "success": False,
                "message": "Slider not found"
            }
        
        # Prepare update data
        update_dict = slider_data.model_dump()
        update_dict["updated_at"] = datetime.now()
        
        # Handle image update if new image provided
        if image_file:
            # Delete old image from Cloudinary
            if current_slider.get("image_public_id"):
                delete_result = delete_image(current_slider["image_public_id"])
                if not delete_result["success"]:
                    print(f"Warning: Failed to delete old image: {delete_result.get('message')}")
            
            # Upload new image to Cloudinary
            image_result = upload_image(image_file)
            if not image_result["success"]:
                return {
                    "success": False,
                    "message": f"Image upload failed: {image_result.get('message')}"
                }
            
            update_dict["image_url"] = image_result["url"]
            update_dict["image_public_id"] = image_result["public_id"]
        
        # Update the slider
        result = slider_col.update_one(
            {"_id": ObjectId(slider_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Slider updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "No changes made"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to update slider: {str(e)}"
        }

def delete_slider_service(slider_id: str) -> dict:
    """Delete a slider (hard delete with Cloudinary image removal)"""
    try:
        from bson import ObjectId
        
        slider_col = collections("sliders")
        
        # Get slider before deletion to remove image from Cloudinary
        slider = slider_col.find_one({"_id": ObjectId(slider_id)})
        if not slider:
            return {
                "success": False,
                "message": "Slider not found"
            }
        
        # Delete image from Cloudinary
        if slider.get("image_public_id"):
            delete_result = delete_image(slider["image_public_id"])
            if not delete_result["success"]:
                print(f"Warning: Failed to delete image from Cloudinary: {delete_result.get('message')}")
        
        # Delete slider from database
        result = slider_col.delete_one({"_id": ObjectId(slider_id)})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Slider deleted successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to delete slider"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete slider: {str(e)}"
        }

def validate_slider_order(order: int) -> bool:
    """Validate that order is a non-negative integer"""
    return isinstance(order, int) and order >= 0