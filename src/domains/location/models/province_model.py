from datetime import datetime, timezone

class ProvinceModel:
    def __init__(self, name_km: str, name_en: str, sort_order: int = 99, is_active: bool = True):
        # រាល់ Field ថ្មីដែលអ្នកចង់ថែមថ្ងៃក្រោយ គ្រាន់តែប្រកាសនៅទីនេះប៉ុណ្ណោះ!
        self.name_km = name_km
        self.name_en = name_en
        self.sort_order = sort_order
        self.is_active = is_active

    def to_create_dict(self) -> dict:
        """ទាញយកទិន្នន័យទាំងអស់សម្រាប់ Create ដោយស្វ័យប្រវត្តិ"""
        now = datetime.now(timezone.utc)
        # self.__dict__.copy() នឹងយក name_km, name_en, sort_order, is_active មកដោយស្វ័យប្រវត្តិ
        data = self.__dict__.copy()
        data["created_at"] = now
        data["updated_at"] = now
        return data

    def to_update_dict(self) -> dict:
        """ទាញយកទិន្នន័យទាំងអស់សម្រាប់ Update ដោយស្វ័យប្រវត្តិ"""
        data = self.__dict__.copy()
        data["updated_at"] = datetime.now(timezone.utc)
        return data

    @staticmethod
    def to_delete_dict() -> dict:
        """រៀបចំទិន្នន័យសម្រាប់ធ្វើ Soft Delete ខេត្ត"""
        return {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        }