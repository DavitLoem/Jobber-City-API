from datetime import datetime
from bson import ObjectId

def CategoryModel(
    name: str,
    icon_url: str = None,
    sort_order: int = 99,   # <-- កែតម្លៃ default ទៅជា 99 តាម Schema ថ្មី
    is_active: bool = True  # <-- បន្ថែម Parameter នេះ
) -> dict:

    return {
        "_id": ObjectId(),
        "name": name,
        "icon_url": icon_url,
        "sort_order": sort_order,
        "is_active": is_active, # <-- យកតម្លៃពី parameter មកដាក់
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }