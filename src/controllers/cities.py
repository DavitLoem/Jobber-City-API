from fastapi import APIRouter, HTTPException
from typing import List
from src.model.cities import CambodianCity, CityCreate, CityUpdate
from src.services.cities import store_validated_city_service, get_all_stored_cities_service, update_city_service, delete_city_service


router = APIRouter(prefix="/api/cities", tags=["Cities"])

@router.post("/", summary="Create multiple cities at once")
async def create_cities(cities: List[CityCreate]): 
    inserted_ids = []
    errors = []
    
    for city in cities:
        result = store_validated_city_service(city.city_name)
        if result.get("success"):
            inserted_ids.append(result.get("city_id"))
        else:
            errors.append({"city": city.city_name, "error": result.get("message")})
            
    return {
        "status": "success",
        "inserted_city_ids": inserted_ids,
        "failed_errors": errors
    }

@router.get("/", summary="Get all Cambodian cities from Database")
async def get_cambodian_cities():
    # ទាញទិន្នន័យផ្ទាល់ពី MongoDB
    cities = get_all_stored_cities_service()
    
    # ប្រសិនបើក្នុង Database មិនទាន់មានទិន្នន័យទាល់តែសោះ (ទទេស្អាត)
    # ឱ្យវាទាញទិន្នន័យលំនាំដើមពី Enum មកបង្ហាញសិន
    if not cities:
        cities = [city.value for city in CambodianCity]

    return {
        "status": "success",
        "data": cities
    }   

@router.put("/{city_id}", summary="Update a city")
async def update_city(city_id: str, city: CityUpdate):
    result = update_city_service(city_id, city.city_name)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    
    return {
        "status": "success",
        "message": result.get("message")
    }


@router.delete("/{city_id}", summary="Delete a city")
async def delete_city(city_id: str):
    result = delete_city_service(city_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    
    return {
        "status": "success",
        "message": result.get("message")
    }