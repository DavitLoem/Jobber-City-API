from datetime import datetime, timezone
from bson import ObjectId

class GenericMasterDataModel:
    def __init__(self, name: str, order: int = 0, is_active: bool = True):
        self.name = name
        self.order = order
        self.is_active = is_active

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "_id": ObjectId(),
            "name": self.name,
            "order": self.order,
            "is_active": self.is_active,
            "created_at": now,
            "updated_at": now
        }

    def to_update_dict(self) -> dict:
        return {
            "name": self.name,
            "order": self.order,
            "is_active": self.is_active,
            "updated_at": datetime.now(timezone.utc)
        }

    @staticmethod
    def to_delete_dict() -> dict:
        # យើងប្រើ Soft Delete (គ្រាន់តែបិទមិនឱ្យ Active) ដើម្បីកុំឱ្យបាត់បង់ប្រវត្តិទិន្នន័យចាស់ៗ
        return {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        }