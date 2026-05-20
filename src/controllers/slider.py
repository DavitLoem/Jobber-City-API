from fastapi import APIRouter, HTTPException, Body, Path, UploadFile, File, Form
from src.model.slider import SliderRequest
from src.services.slider import (
    create_slider_service,
    get_all_sliders_service,
    get_slider_by_id_service,
    update_slider_service,
    delete_slider_service,
    validate_slider_order
)

router = APIRouter(prefix="/api/slider", tags=["Slider"])

@router.post("/sliders", summary="Create a new slider")
async def create_slider(
    image: UploadFile = File(..., description="Slider image file"),
    title: str = Form(..., min_length=5, max_length=150),
    button_text: str = Form("Read more", max_length=30),
    link_url: str = Form(None),
    order: int = Form(0, ge=0),
    is_active: bool = Form(True)
):

    if not validate_slider_order(order):
        raise HTTPException(status_code=400, detail="Order must be a non-negative integer")
    
    slider_data = SliderRequest(
        title=title,
        button_text=button_text,
        link_url=link_url,
        order=order,
        is_active=is_active
    )
    
    result = create_slider_service(slider_data, image.file)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "status": "success",
        "message": result["message"],
        "slider_id": result["slider_id"],
        "image_url": result.get("image_url")
    }

@router.get("/sliders", summary="Get all active sliders")
async def get_all_sliders():
    """Get all active sliders ordered by display order"""
    result = get_all_sliders_service()
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return {
        "status": "success",
        "data": result["data"],
        "count": result["count"]
    }

@router.get("/sliders/{slider_id}", summary="Get a specific slider")
async def get_slider_by_id(slider_id: str = Path(..., description="Slider ID")):
    """Get a specific slider by its ID"""
    result = get_slider_by_id_service(slider_id)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return {
        "status": "success",
        "data": result["data"]
    }

@router.put("/sliders/{slider_id}", summary="Update a slider")
async def update_slider(
    slider_id: str = Path(..., description="Slider ID"),
    image: UploadFile = File(None, description="Optional new slider image"),
    title: str = Form(..., min_length=5, max_length=150),
    button_text: str = Form("Read more", max_length=30),
    link_url: str = Form(None),
    order: int = Form(0, ge=0),
    is_active: bool = Form(True)
):
    """Update an existing slider with optional image update"""
 
    if not validate_slider_order(order):
        raise HTTPException(status_code=400, detail="Order must be a non-negative integer")

    slider_data = SliderRequest(
        title=title,
        button_text=button_text,
        link_url=link_url,
        order=order,
        is_active=is_active
    )

    image_file = image.file if image and image.filename else None
    
    result = update_slider_service(slider_id, slider_data, image_file)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "status": "success",
        "message": result["message"]
    }

@router.delete("/sliders/{slider_id}", summary="Delete a slider")
async def delete_slider(slider_id: str = Path(..., description="Slider ID")):
    """Soft delete a slider (sets is_active to False)"""
    result = delete_slider_service(slider_id)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return {
        "status": "success",
        "message": result["message"]
    }

@router.get("/sliders/validate-order/{order}", summary="Validate slider order")
async def validate_order(order: int = Path(..., description="Order value to validate")):
    """Validate if an order value is acceptable"""
    is_valid = validate_slider_order(order)
    
    return {
        "status": "success",
        "is_valid": is_valid,
        "order": order,
        "message": "Order is valid" if is_valid else "Order must be a non-negative integer"
    }