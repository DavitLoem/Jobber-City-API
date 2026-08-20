from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from fastapi import HTTPException

from src.core.mongo import (
    conversations_collection,
    chat_messages_collection,
    device_tokens_collection,
    users_collection,
    seeker_profiles_collection,
    company_profiles_collection,
)
from src.domains.chat.models.chat_model import ConversationModel, MessageModel
from src.domains.chat.services.connection_manager import connection_manager
from src.domains.chat.services.push_service import send_chat_push_notification


class ChatService:

    # ==========================================
    # 🎯 Helpers (Private)
    # ==========================================

    async def _get_display_info(self, user_id: ObjectId, role: str) -> dict:
        """ទាញយកឈ្មោះ + រូបភាព សម្រាប់បង្ហាញក្នុង Chat List / Header (Lightweight, មិនទាញ Profile ពេញលេញ)"""
        user = await users_collection.find_one({"_id": user_id})
        if not user:
            return {"user_id": str(user_id), "name": "Unknown User", "avatar_url": None, "role": role, "is_online": False}

        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get("email", "User")
        avatar_url = user.get("avatar_url")

        # 🎯 សម្រាប់ Employer យើងចង់បង្ហាញ Logo + ឈ្មោះក្រុមហ៊ុន (មិនមែនឈ្មោះផ្ទាល់ខ្លួន HR)
        if role == "employer":
            company = await company_profiles_collection.find_one({"user_id": user_id})
            if company:
                name = company.get("company_name", name)
                avatar_url = company.get("logo_url", avatar_url)
        elif role == "seeker":
            seeker = await seeker_profiles_collection.find_one({"user_id": user_id})
            if seeker and seeker.get("image_url"):
                avatar_url = seeker.get("image_url")

        return {
            "user_id": str(user_id),
            "name": name,
            "avatar_url": avatar_url,
            "role": role,
            "is_online": connection_manager.is_online(str(user_id)),
        }

    def _format_message(self, msg: dict) -> dict:
        # 🎯 សំខាន់៖ created_at ត្រូវបំប្លែងទៅជា ISO String ជានិច្ច មុននឹងយកទៅប្រើក្នុង
        # WebSocket payload។ REST responses ឆ្លងកាត់ FastAPI's jsonable_encoder ដោយស្វ័យប្រវត្តិ
        # ដូច្នេះ datetime object ធម្មតាគ្មានបញ្ហាទេ តែ websocket.send_json() ប្រើ json.dumps()
        # ធម្មតា (មិនចេះបំប្លែង datetime ទេ) — បើមិនបំប្លែងទុកជាមុន Server នឹង Raise
        # TypeError ស្ងាត់ៗពេល Broadcast ហើយ Connection នោះនឹងត្រូវសម្គាល់ខុសថា "Dead"។
        created_at = msg.get("created_at")
        return {
            "id": str(msg["_id"]),
            "conversation_id": str(msg["conversation_id"]),
            "sender_id": str(msg["sender_id"]),
            "sender_role": msg.get("sender_role"),
            "message_type": msg.get("message_type", "text"),
            "content": msg.get("content", ""),
            "attachment_url": msg.get("attachment_url"),
            "status": msg.get("status", "sent"),
            "client_temp_id": msg.get("client_temp_id"),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        }

    async def _format_conversation(self, convo: dict, current_user_id: str) -> dict:
        is_seeker_viewing = str(convo["seeker_id"]) == current_user_id
        other_id = convo["employer_id"] if is_seeker_viewing else convo["seeker_id"]
        other_role = "employer" if is_seeker_viewing else "seeker"
        other_party = await self._get_display_info(other_id, other_role)

        return {
            "id": str(convo["_id"]),
            "job_id": str(convo["job_id"]) if convo.get("job_id") else None,
            "other_party": other_party,
            "last_message": convo.get("last_message"),
            "last_message_type": convo.get("last_message_type"),
            "last_message_at": convo.get("last_message_at"),
            "last_sender_id": str(convo["last_sender_id"]) if convo.get("last_sender_id") else None,
            "unread_count": convo.get("unread_count", {}).get(current_user_id, 0),
            "created_at": convo.get("created_at"),
        }

    async def _assert_participant(self, conversation_id: str, user_id: str) -> dict:
        """ត្រឡប់ Conversation Document ដើម Raw (មិនទាន់ Format) បើ user_id នេះជាសមាជិកពិតប្រាកដ"""
        if not ObjectId.is_valid(conversation_id):
            raise HTTPException(status_code=400, detail="Invalid conversation ID.")

        convo = await conversations_collection.find_one({"_id": ObjectId(conversation_id)})
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        if user_id not in [str(p) for p in convo["participant_ids"]]:
            raise HTTPException(status_code=403, detail="You are not a participant of this conversation.")

        return convo

    async def get_conversation_for_participant(self, conversation_id: str, user_id: str) -> dict:
        """Public wrapper - ត្រូវការសម្រាប់ WebSocket Router (ឧ. Typing Indicator) ដែលចង់ដឹងថា
        ភាគីម្ខាងទៀតជានរណា ដោយមិនចាំបាច់ចូលដល់ Method Private"""
        return await self._assert_participant(conversation_id, user_id)

    # ==========================================
    # 🎯 Conversations
    # ==========================================

    async def get_or_create_conversation(self, current_user: dict, other_user_id: str, job_id: Optional[str]) -> dict:
        if not ObjectId.is_valid(other_user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID.")

        current_role = current_user.get("role")
        if current_role not in ["seeker", "employer"]:
            raise HTTPException(status_code=403, detail="Only seekers and employers can start a chat.")

        if str(current_user["_id"]) == other_user_id:
            raise HTTPException(status_code=400, detail="You cannot start a conversation with yourself.")

        other_user = await users_collection.find_one({"_id": ObjectId(other_user_id)})
        if not other_user:
            raise HTTPException(status_code=404, detail="The other user was not found.")

        other_role = other_user.get("role")
        if {current_role, other_role} != {"seeker", "employer"}:
            raise HTTPException(status_code=400, detail="Chat is only allowed between a seeker and an employer.")

        if job_id and not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="Invalid job ID.")

        if current_role == "seeker":
            seeker_id, employer_id = current_user["_id"], ObjectId(other_user_id)
        else:
            seeker_id, employer_id = ObjectId(other_user_id), current_user["_id"]

        # 🎯 មួយគូ Seeker-Employer មានតែ Conversation មួយប៉ុណ្ណោះ (Get-or-Create Pattern)
        # ការចាប់ផ្តើម Chat ថ្មីលើក Job ថ្មីមួយទៀត នៅតែបន្តក្នុង Thread ចាស់ដដែល
        existing = await conversations_collection.find_one({"seeker_id": seeker_id, "employer_id": employer_id})
        if existing:
            if job_id and not existing.get("job_id"):
                await conversations_collection.update_one(
                    {"_id": existing["_id"]}, {"$set": {"job_id": ObjectId(job_id)}}
                )
                existing["job_id"] = ObjectId(job_id)
            return await self._format_conversation(existing, str(current_user["_id"]))

        model = ConversationModel(seeker_id=seeker_id, employer_id=employer_id, job_id=job_id)
        new_convo = model.to_create_dict()
        await conversations_collection.insert_one(new_convo)

        return await self._format_conversation(new_convo, str(current_user["_id"]))

    async def list_conversations(self, user_id: str, page: int = 1, limit: int = 20) -> List[dict]:
        skip = (page - 1) * limit
        cursor = (
            conversations_collection.find({"participant_ids": ObjectId(user_id)})
            .sort("last_message_at", -1)
            .skip(skip)
            .limit(limit)
        )

        results = []
        async for convo in cursor:
            results.append(await self._format_conversation(convo, user_id))
        return results

    # ==========================================
    # 🎯 Messages
    # ==========================================

    async def get_messages(self, conversation_id: str, user_id: str, before: Optional[str], limit: int = 30) -> dict:
        await self._assert_participant(conversation_id, user_id)

        query = {"conversation_id": ObjectId(conversation_id)}
        if before:
            if not ObjectId.is_valid(before):
                raise HTTPException(status_code=400, detail="Invalid cursor.")
            # 🎯 Cursor-based Pagination៖ ប្រើ _id (ObjectId មាន Timestamp កប់ក្នុងខ្លួនស្រាប់)
            # ជាចំណុចកាត់ ជំនួសការប្រើ .skip(n) ដែលយឺតបន្តិចម្តងៗពេល History វែងឡើងៗ
            query["_id"] = {"$lt": ObjectId(before)}

        # ទាញច្រើនជាង limit ១ ដើម្បីដឹងថាមាន Page បន្តទៀត (has_more) ដោយមិនចាំបាច់ Query COUNT ដាច់ដោយឡែក
        cursor = chat_messages_collection.find(query).sort("_id", -1).limit(limit + 1)
        raw_messages = [m async for m in cursor]

        has_more = len(raw_messages) > limit
        raw_messages = raw_messages[:limit]
        raw_messages.reverse()  # ត្រឡប់ទៅលំដាប់ពេលវេលា (ចាស់ -> ថ្មី) សម្រាប់បង្ហាញត្រង់ក្នុង Chat UI

        return {
            "messages": [self._format_message(m) for m in raw_messages],
            "has_more": has_more,
        }

    async def send_message(
        self,
        conversation_id: str,
        sender: dict,
        content: str,
        message_type: str = "text",
        attachment_url: Optional[str] = None,
        client_temp_id: Optional[str] = None,
    ) -> dict:
        sender_id = sender["_id"]
        convo = await self._assert_participant(conversation_id, str(sender_id))

        recipient_id = convo["employer_id"] if convo["seeker_id"] == sender_id else convo["seeker_id"]
        sender_role = "seeker" if convo["seeker_id"] == sender_id else "employer"

        # ១. Persist ចូល Database សិន (Database ជា Source of Truth - "Write-then-Broadcast")
        # បើ Broadcast បរាជ័យក្រោយពី Save រួច Message នៅតែមិនបាត់ អាចទាញយកវិញបានតាម REST History
        model = MessageModel(
            conversation_id=convo["_id"],
            sender_id=sender_id,
            sender_role=sender_role,
            message_type=message_type,
            content=content,
            attachment_url=attachment_url,
            client_temp_id=client_temp_id,
        )
        new_message = model.to_create_dict()
        await chat_messages_collection.insert_one(new_message)

        # ២. Update Conversation Summary (Last Message Preview + Unread Count របស់អ្នកទទួល)
        preview = content if message_type == "text" else f"[{message_type.capitalize()}]"
        recipient_key = str(recipient_id)
        await conversations_collection.update_one(
            {"_id": convo["_id"]},
            {
                "$set": {
                    "last_message": preview[:200],
                    "last_message_type": message_type,
                    "last_message_at": new_message["created_at"],
                    "last_sender_id": sender_id,
                    "updated_at": new_message["created_at"],
                },
                "$inc": {f"unread_count.{recipient_key}": 1},
            },
        )

        formatted = self._format_message(new_message)

        # ៣. ផ្ញើ Real-time ទៅកាន់ Device ទាំងអស់ (រួមទាំង Sender ខ្លួនឯង ដើម្បី Sync ច្រើន Device
        # ក្នុងពេលតែមួយ - ឧ. គាត់ Login ទាំងលើទូរស័ព្ទ និង Tablet)
        payload = {"type": "new_message", "data": formatted}
        await connection_manager.send_to_user(str(sender_id), payload)
        recipient_is_online = await connection_manager.send_to_user(recipient_key, payload)

        # ៤. បើអ្នកទទួល Offline (គ្មាន WebSocket ណាមួយ Active សោះ) -> ផ្ញើ Push Notification ជំនួសវិញ
        if not recipient_is_online:
            await self._push_new_message_notification(recipient_id, sender, preview, str(convo["_id"]))

        return formatted

    async def _push_new_message_notification(self, recipient_id: ObjectId, sender: dict, preview: str, conversation_id: str):
        tokens_cursor = device_tokens_collection.find({"user_id": recipient_id})
        tokens = [t["fcm_token"] async for t in tokens_cursor]
        if not tokens:
            return

        sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip() or "New message"

        result = await send_chat_push_notification(
            fcm_tokens=tokens,
            title=sender_name,
            body=preview,
            data={"type": "chat_message", "conversation_id": conversation_id},
        )

        # 🎯 សម្អាត Token ដែលលែងប្រើការ (App ត្រូវបានលុប/Uninstall) ចេញពី Database ស្វ័យប្រវត្តិ
        invalid = result.get("invalid_tokens") or []
        if invalid:
            await device_tokens_collection.delete_many({"fcm_token": {"$in": invalid}})

    async def mark_as_read(self, conversation_id: str, user_id: str) -> dict:
        convo = await self._assert_participant(conversation_id, user_id)
        now = datetime.now(timezone.utc)

        await conversations_collection.update_one(
            {"_id": convo["_id"]},
            {"$set": {f"unread_count.{user_id}": 0, f"last_read_at.{user_id}": now}},
        )

        # ជូនដំណឹងទៅភាគីម្ខាងទៀត (បើ Online) ថា Message ត្រូវបានអានហើយ ដើម្បីបង្ហាញសញ្ញា "Seen" លើ UI
        other_id = convo["employer_id"] if str(convo["seeker_id"]) == user_id else convo["seeker_id"]
        await connection_manager.send_to_user(
            str(other_id),
            {
                "type": "read_receipt",
                "conversation_id": conversation_id,
                "reader_id": user_id,
                "read_at": now.isoformat(),
            },
        )
        return {"success": True}

    # ==========================================
    # 🎯 Device Tokens (Push Notification Registration)
    # ==========================================

    async def register_device_token(self, user_id: str, fcm_token: str, platform: str) -> dict:
        # 🎯 Upsert តាម fcm_token (មិនមែនតាម user_id) ព្រោះ Token តែមួយអាចផ្លាស់ប្តូរម្ចាស់
        # បានពេល Logout គណនីមួយ ហើយ Login គណនីមួយទៀតនៅលើ Device ដដែល
        await device_tokens_collection.update_one(
            {"fcm_token": fcm_token},
            {
                "$set": {
                    "user_id": ObjectId(user_id),
                    "platform": platform,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {"_id": ObjectId(), "created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        return {"success": True}

    async def remove_device_token(self, fcm_token: str) -> dict:
        await device_tokens_collection.delete_one({"fcm_token": fcm_token})
        return {"success": True}


chat_service = ChatService()
