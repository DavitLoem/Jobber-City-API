from bson import ObjectId
from fastapi import HTTPException
from src.domains.master_data.models.generic_master_data_model import GenericMasterDataModel
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate

class GenericMasterDataService:
    def __init__(self, collection):
        # 🎯 ទទួលយក Collection ដែលបាន Import ពី mongo.py
        self.collection = collection
        # ទាញយកឈ្មោះ Collection អូតូ (ឧ. 'skills') សម្រាប់បង្ហាញក្នុង Error Message
        self.collection_name = collection.name 

    def _format_response(self, item: dict) -> dict:
        """បំប្លែង Object ពី MongoDB ទៅជាទម្រង់ដែល Schema ត្រូវការ"""
        if not item: return None
        return {
            "id": str(item["_id"]),
            "name": item.get("name", ""),
            "order": item.get("order", 0),
            "is_active": item.get("is_active", True)
        }

    async def get_all(
        self, 
        search_term: str = None, 
        status_filter: str = "all" 
    ) -> list[dict]:
        """
        ទាញយកទិន្នន័យទាំងអស់ ដោយអាច Search តាមឈ្មោះ និង Filter តាម Status។
        
        Args:
            search_term (str, optional): ពាក្យស្វែងរក.
            status_filter (str, optional): "all" (ទាំងអស់), "active", ឬ "inactive".
        """
        query = {}
        
        # 1. បន្ថែមលក្ខខណ្ឌ Search តាមឈ្មោះ (Case-Insensitive)
        if search_term:
            query["name"] = {"$regex": search_term, "$options": "i"}

        # 2. បន្ថែមលក្ខខណ្ឌ Filter តាម Status
        if status_filter == "active":
            query["is_active"] = True
        elif status_filter == "inactive":
            query["is_active"] = False

        # តម្រៀបតាម order ជាចម្បង បើ order ស្មើគ្នា តម្រៀបតាមឈ្មោះ (A-Z)
        cursor = self.collection.find(query).sort([("order", 1), ("name", 1)])
        items = await cursor.to_list(length=None)
        
        return [self._format_response(item) for item in items]

    async def create(self, data: GenericMasterDataCreate) -> dict:
        """បង្កើតទិន្នន័យថ្មី"""
        existing = await self.collection.find_one({"name": {"$regex": f"^{data.name}$", "$options": "i"}})
        if existing:
            raise HTTPException(status_code=400, detail=f"'{data.name}' already exists in {self.collection_name}.")

        new_model = GenericMasterDataModel(name=data.name, order=data.order, is_active=data.is_active)
        new_dict = new_model.to_create_dict()
        
        await self.collection.insert_one(new_dict)
        return self._format_response(new_dict)

    async def update(self, item_id: str, data: GenericMasterDataUpdate) -> dict:
        """កែប្រែទិន្នន័យ"""
        if not ObjectId.is_valid(item_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update.")
        if "name" in update_data:
            existing = await self.collection.find_one({
                "name": {"$regex": f"^{update_data['name']}$", "$options": "i"},
                "_id": {"$ne": ObjectId(item_id)}
            })
            if existing:
                raise HTTPException(status_code=400, detail=f"Name '{update_data['name']}' already exists.")

        update_dict = GenericMasterDataModel(**update_data).to_update_dict()
        
        updated_item = await self.collection.find_one_and_update(
            {"_id": ObjectId(item_id)},
            {"$set": update_dict},
            return_document=True
        )

        if not updated_item:
            raise HTTPException(status_code=404, detail="Item not found.")

        return self._format_response(updated_item)

    async def delete(self, item_id: str) -> bool:
        """លុបទិន្នន័យ (Soft Delete)"""
        if not ObjectId.is_valid(item_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")

        delete_dict = GenericMasterDataModel.to_delete_dict()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": delete_dict}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Item not found or already deleted.")

        return True