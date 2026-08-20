from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional


class ConversationModel:
    """
    ១ Conversation = ការសន្ទនាមួយចន្លោះ Seeker ១ នាក់ និង Employer ១ នាក់។
    យើងរក្សាទុកតែ Thread មួយប៉ុណ្ណោះក្នុងមួយគូ (seeker, employer) ដើម្បីកុំឱ្យមាន Chat
    ច្រើនច្រាល់គ្នា ទោះបីជាពួកគេនិយាយគ្នាអំពីការងារច្រើនតួក៏ដោយ
    (job_id គ្រាន់តែជាបរិបទដំបូងសម្រាប់បង្ហាញ "Job Card" លើកម្ពូល Chat ប៉ុណ្ណោះ)។
    """

    def __init__(
        self,
        seeker_id: str | ObjectId,
        employer_id: str | ObjectId,
        job_id: Optional[str | ObjectId] = None,
    ):
        self.seeker_id = ObjectId(seeker_id) if isinstance(seeker_id, str) else seeker_id
        self.employer_id = ObjectId(employer_id) if isinstance(employer_id, str) else employer_id
        self.job_id = (ObjectId(job_id) if isinstance(job_id, str) else job_id) if job_id else None

        # 🎯 Array នេះសម្រាប់ Query លឿន៖ "រកគ្រប់ Conversation ដែល User នេះជាសមាជិក"
        # ប្រើ { participant_ids: user_id } ជំនួសការ $or លើ seeker_id/employer_id
        self.participant_ids = [self.seeker_id, self.employer_id]

        self.last_message = None
        self.last_message_type = None
        self.last_message_at = None
        self.last_sender_id = None

        # 🎯 រាប់ Message មិនទាន់អាន ដាច់ដោយឡែកសម្រាប់ User ម្នាក់ៗ (Key = user_id ជា String)
        # Denormalized counter -> O(1) ពេល Update មិនចាំបាច់ COUNT() លើ Messages collection
        self.unread_count = {str(self.seeker_id): 0, str(self.employer_id): 0}

        # 🎯 ពេលវេលាចុងក្រោយដែល User ម្នាក់ៗបានអានសារ (សម្រាប់គណនា Read Receipt "Seen")
        self.last_read_at = {str(self.seeker_id): None, str(self.employer_id): None}

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["_id"] = ObjectId()
        data["created_at"] = now
        data["updated_at"] = now
        return data


class MessageModel:
    ALLOWED_TYPES = ["text", "image", "file"]

    def __init__(
        self,
        conversation_id: str | ObjectId,
        sender_id: str | ObjectId,
        sender_role: str,
        message_type: str = "text",
        content: str = "",
        attachment_url: Optional[str] = None,
        client_temp_id: Optional[str] = None,
    ):
        self.conversation_id = ObjectId(conversation_id) if isinstance(conversation_id, str) else conversation_id
        self.sender_id = ObjectId(sender_id) if isinstance(sender_id, str) else sender_id
        self.sender_role = sender_role
        self.message_type = message_type if message_type in self.ALLOWED_TYPES else "text"
        self.content = content
        self.attachment_url = attachment_url

        # 🎯 client_temp_id ជួយ Flutter ធ្វើ Optimistic UI៖ Client បង្កើត UUID លើ Local
        # ជាមុនសិន បង្ហាញលើ Screen ភ្លាមៗ រួច Server បញ្ជូន Temp ID នេះមកវិញជាមួយ Message
        # ពិតប្រាកដ ដើម្បីឱ្យ Flutter ដឹងថាត្រូវជំនួស Message បណ្តោះអាសន្ននឹង Message ពិត
        self.client_temp_id = client_temp_id
        self.status = "sent"

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["_id"] = ObjectId()
        data["created_at"] = now
        return data


class DeviceTokenModel:
    """ទុក FCM Token របស់ទូរស័ព្ទនីមួយៗ ដើម្បីផ្ញើ Push Notification ពេល User Offline"""

    def __init__(self, user_id: str | ObjectId, fcm_token: str, platform: str = "android"):
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.fcm_token = fcm_token
        self.platform = platform if platform in ["android", "ios"] else "android"

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["_id"] = ObjectId()
        data["created_at"] = now
        data["updated_at"] = now
        return data
