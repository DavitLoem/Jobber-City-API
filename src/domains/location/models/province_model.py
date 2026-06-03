from datetime import datetime, timezone

def create_province_model(
    name_km: str, 
    name_en: str, 
    sort_order: int = 99, 
    is_active: bool = True
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "name_km": name_km,
        "name_en": name_en,
        "sort_order": sort_order,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now
    }