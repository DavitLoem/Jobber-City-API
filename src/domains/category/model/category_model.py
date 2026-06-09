from datetime import datetime, timezone
from typing import Optional

class CategoryModel:
    def __init__(self, name: str, icon_url: Optional[str] = None, sort_order: int = 99, is_active: bool = True):
        self.name = name
        self.icon_url = icon_url
        self.sort_order = sort_order
        self.is_active = is_active

    def to_create_dict(self) -> dict:
        """វេចខ្ចប់ទិន្នន័យសម្រាប់ Insert ចូល Database (មានទាំង created_at និង updated_at)"""
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    def to_update_dict(self) -> dict:
        """វេចខ្ចប់ទិន្នន័យសម្រាប់ Update (ផ្លាស់ប្តូរតែ updated_at)"""
        data = self.__dict__.copy()
        data["updated_at"] = datetime.now(timezone.utc)
        return data

    @staticmethod
    def to_delete_dict() -> dict:
        """វេចខ្ចប់ទិន្នន័យសម្រាប់ Soft Delete"""
        return {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        }