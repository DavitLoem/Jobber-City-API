from fastapi import APIRouter, HTTPException, status
from typing import List 
from src.model.expertise import Expertise, ExpertisePost, ExpertiseUpdate
from src.services.expertise import (
    get_all_expertises_service,
    store_validated_expertise_service,
    update_expertise_service,
    delete_expertise_service
)

router = APIRouter(prefix="/api/expertise", tags=["Expertise"])

@router.get("/", summary="Get all expertise from Database")
async def get_expertise_fields():
   
    expertises = get_all_expertises_service()
    if not expertises:
        expertises = [exp.value for exp in Expertise]
    return {
        "status": "success",
        "data": expertises
    }

@router.post("/", summary="Create multiple expertises at once")
async def create_multiple_expertises(payloads: List[ExpertisePost]):  # ✅ ប្តូរទៅជា List
    inserted_ids = []
    
    for payload in payloads:
        result = store_validated_expertise_service(payload.expertise.value)
        if result.get("success"):
            inserted_ids.append(result.get("expertise_id"))
            
    return {
        "status": "success",
        "inserted_ids": inserted_ids
    }

@router.put("/{expertise_id}", summary="Update/Put an existing expertise")
async def update_expertise(expertise_id: str, payload: ExpertiseUpdate):
    result = update_expertise_service(expertise_id, payload.expertise.value)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
    return {
        "status": "success",
        "message": result.get("message")
    }

@router.delete("/{expertise_id}", summary="Delete an expertise")
async def delete_expertise(expertise_id: str):
    result = delete_expertise_service(expertise_id)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
    return {
        "status": "success",
        "message": result.get("message")
    }