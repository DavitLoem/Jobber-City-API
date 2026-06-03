from datetime import datetime, timezone
from bson import ObjectId

def create_district_model(
    province_id: str | ObjectId, 
    name_km: str, 
    name_en: str, 
    sort_order: int = 99, 
    is_active: bool = True
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        # បំប្លែង String ទៅជា ObjectId ស្វ័យប្រវត្តិ មុននឹង Save ចូល DB
        "province_id": ObjectId(province_id) if isinstance(province_id, str) else province_id,
        "name_km": name_km,
        "name_en": name_en,
        "sort_order": sort_order,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now
    }