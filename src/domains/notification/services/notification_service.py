from bson import ObjectId
from datetime import datetime, timezone
import json
import os

import firebase_admin
from firebase_admin import credentials, messaging
from src.core.mongo import notifications_collection, users_collection
from src.domains.notification.models.notification_model import NotificationResponse

if not firebase_admin._apps:
    # ១. សាកល្បងទាញយកពី Environment Variables (សម្រាប់ Railway)
    firebase_env = os.getenv("FIREBASE_CREDENTIALS")
    
    if firebase_env:
        # បម្លែងអក្សរ String ពី Railway ទៅជា JSON Object វិញ
        cred_dict = json.loads(firebase_env)
        cred = credentials.Certificate(cred_dict)
        print("✅ Loaded Firebase credentials from Environment Variable.")
    else:
        # ២. បើគ្មាន Env ទេ គឺទាញយកពី File (សម្រាប់ពេល Run លើកុំព្យូទ័រ Local)
        # ការពារការវង្វេង Path ដោយថយក្រោយ ៤ កម្រិត (services -> notification -> domains -> src -> Root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))
        file_path = os.path.join(root_dir, "serviceAccountKey.json")
        
        cred = credentials.Certificate(file_path)
        print("✅ Loaded Firebase credentials from Local JSON file.")
        
    firebase_admin.initialize_app(cred)

class NotificationService:

    # 🟢 ១. មុខងារសម្រាប់បញ្ជាបង្កើត Notification (Trigger)
    async def create_notification(self, user_id: str, title: str, message: str, notif_type: str, related_id: str = None) -> bool:
        """
        អនុគមន៍កណ្តាលសម្រាប់បង្កើត Notification ថ្មី និងបាញ់ Push Notification (FCM)
        """
        # ផ្នែកទី ១៖ រក្សាទុកចូលក្នុង MongoDB (ដូចដើម)
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

        # ផ្នែកទី ២៖ បាញ់ Push Notification ទៅកាន់ Firebase
        try:
            # ទាញយក Profile របស់ User ដើម្បីយក fcm_token
            user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            user_doc = await users_collection.find_one({"_id": user_oid})
            
            if user_doc and "fcm_token" in user_doc:
                fcm_token = user_doc["fcm_token"]
                
                # រៀបចំទម្រង់សារដែលត្រូវផ្ញើ
                fcm_message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=message,
                    ),
                    data={
                        "type": notif_type, 
                        "related_id": str(related_id) if related_id else ""
                    },
                    token=fcm_token, # បញ្ជូនទៅកាន់ឧបករណ៍នេះ
                )
                
                # បញ្ជាឱ្យ Firebase ផ្ញើសារ
                messaging.send(fcm_message)
                print(f"✅ Successfully sent FCM to user: {user_id}")
            else:
                print(f"⚠️ User {user_id} does not have an FCM token.")
                
        except Exception as e:
            print(f"❌ Error sending FCM notification: {e}")

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
    
    async def update_fcm_token(self, user_id: str, fcm_token: str) -> bool:
        """រក្សាទុក FCM Token របស់ User ទៅក្នុង Database"""
        from bson import ObjectId
        from src.core.mongo import users_collection
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"fcm_token": fcm_token}}
        )
        
        # 🟢 ប្រើប្រាស់ result.matched_count ដើម្បីបញ្ជាក់ថាពិតជារកឃើញគណនីមែន
        return result.matched_count > 0

# Create Singleton Instance
notification_service = NotificationService()