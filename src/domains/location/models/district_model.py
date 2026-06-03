from datetime import datetime, timezone
from bson import ObjectId

class DistrictModel:
    def __init__(self, province_id: str | ObjectId, name_km: str, name_en: str, sort_order: int = 99, is_active: bool = True):
        # ចាត់ចែងការបំប្លែង ObjectId នៅទីនេះតែម្តងគត់!
        self.province_id = ObjectId(province_id) if isinstance(province_id, str) else province_id
        self.name_km = name_km
        self.name_en = name_en
        self.sort_order = sort_order
        self.is_active = is_active

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    def to_update_dict(self) -> dict:
        data = self.__dict__.copy()
        data["updated_at"] = datetime.now(timezone.utc)
        return data

    @staticmethod
    def to_delete_dict() -> dict:
        return {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        }