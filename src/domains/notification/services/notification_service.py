from bson import ObjectId
from datetime import datetime, timezone
from src.core.mongo import notifications_collection
from src.domains.notification.models.notification_model import NotificationResponse

class NotificationService:

    # 🟢 ១. មុខងារសម្រាប់បញ្ជាបង្កើត Notification (Trigger)
    async def create_notification(self, user_id: str, title: str, message: str, notif_type: str, related_id: str = None) -> bool:
        """
        អនុគមន៍កណ្តាលសម្រាប់បង្កើត Notification ថ្មី (ហៅដោយ Service ផ្សេងៗ)
        """
        new_notif = {
            "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "related_id": related_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        result = await notifications_collection.insert_one(new_notif)
        return result.acknowledged

    # 🟢 ២. មុខងាររាប់ចំនួនសារដែលមិនទាន់អាន (សម្រាប់ចំណុចក្រហមលើកណ្តឹង)
    async def get_unread_count(self, user_id: str) -> int:
        user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        count = await notifications_collection.count_documents({
            "user_id": user_oid,
            "is_read": False
        })
        return count

    # 🟢 ៣. មុខងារទាញយកបញ្ជី Notification ទាំងអស់ (សម្រាប់បង្ហាញក្នុងទំព័រ Notification)
    async def get_my_notifications(self, user_id: str, limit: int = 20, skip: int = 0):
        user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        
        cursor = notifications_collection.find({"user_id": user_oid}).sort("created_at", -1).skip(skip).limit(limit)
        notifications = await cursor.to_list(length=limit)
        
        total = await notifications_collection.count_documents({"user_id": user_oid})
        
        result_list = []
        for notif in notifications:
            result_list.append(NotificationResponse(
                id=str(notif["_id"]),
                user_id=str(notif["user_id"]),
                title=notif.get("title", ""),
                message=notif.get("message", ""),
                type=notif.get("type", "general"),
                related_id=notif.get("related_id"),
                is_read=notif.get("is_read", False),
                created_at=notif.get("created_at")
            ))
            
        return result_list, total

    # 🟢 ៤. មុខងារសម្គាល់ថាបានអានទាំងអស់ (Mark all as read)
    async def mark_all_as_read(self, user_id: str) -> bool:
        user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        await notifications_collection.update_many(
            {"user_id": user_oid, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return True
    
    async def mark_single_as_read(self, user_id: str, notification_id: str) -> bool:
        if not ObjectId.is_valid(notification_id):
            return False

        # ធ្វើការ Update ដោយប្រាកដថា User ID ត្រូវគ្នា (ការពារការ Update ឆ្លងគណនី)
        result = await notifications_collection.update_one(
            {
                "_id": ObjectId(notification_id),
                "user_id": ObjectId(user_id) 
            },
            {"$set": {"is_read": True}}
        )

        # ត្រឡប់ True ប្រសិនបើស្វែងរកឃើញ និងធ្វើការ Update បានជោគជ័យ
        return result.modified_count > 0

# Create Singleton Instance
notification_service = NotificationService()