from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from bson import ObjectId

from src.core.security import verify_token
from src.core.mongo import users_collection
from src.domains.chat.services.connection_manager import connection_manager
from src.domains.chat.services.chat_service import chat_service

router = APIRouter(tags=["Mobile - Chat WebSocket"])


async def _authenticate_ws(token: str):
    """
    WebSocket មិនអាចប្រើ `Authorization: Bearer <token>` Header តាមបែប HTTPBearer
    ធម្មតាបានស្រួលនោះទេ (ជាពិសេស Client លើ Web/Browser)។ ដូច្នេះយើងទទួល JWT
    Access Token ដដែលតាម Query String វិញ៖

        wss://your-api.com/api/chat/ws?token=<access_token>

    ⚠️ សុវត្ថិភាព៖ លើ Production ត្រូវប្រើ wss:// (TLS) ជានិច្ច ដើម្បីកុំឱ្យ Token
    លេចធ្លាយតាម Access Log របស់ Proxy/Load Balancer នៅចន្លោះផ្លូវ។
    """
    try:
        payload = verify_token(token)
    except HTTPException:
        return None

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        return None

    return await users_collection.find_one({"_id": ObjectId(user_id)})


async def _handle_event(user: dict, user_id: str, raw: dict, websocket: WebSocket):
    event_type = raw.get("type")

    if event_type == "send_message":
        await chat_service.send_message(
            conversation_id=raw.get("conversation_id"),
            sender=user,
            content=raw.get("content", ""),
            message_type=raw.get("message_type", "text"),
            attachment_url=raw.get("attachment_url"),
            client_temp_id=raw.get("client_temp_id"),
        )

    elif event_type == "typing":
        # 🎯 Typing Indicator មិន Persist ចូល Database ទេ (Ephemeral) - គ្រាន់តែបញ្ជូនបន្តទៅ
        # ភាគីម្ខាងទៀតដែលកំពុង Online ភ្លាមៗ ដើម្បីបង្ហាញ "... is typing"
        convo_id = raw.get("conversation_id")
        convo = await chat_service.get_conversation_for_participant(convo_id, user_id)
        other_id = convo["employer_id"] if str(convo["seeker_id"]) == user_id else convo["seeker_id"]
        await connection_manager.send_to_user(
            str(other_id),
            {
                "type": "typing",
                "conversation_id": convo_id,
                "user_id": user_id,
                "is_typing": bool(raw.get("is_typing", True)),
            },
        )

    elif event_type == "read":
        await chat_service.mark_as_read(raw.get("conversation_id"), user_id)

    elif event_type == "ping":
        # 🎯 Heartbeat - Client គួរផ្ញើរៀងរាល់ ~25s ដើម្បីរក្សា Connection ឱ្យរស់ កុំឱ្យ
        # Proxy/Load Balancer កាត់ Connection ចោលព្រោះគិតថា Idle
        await websocket.send_json({"type": "pong"})

    else:
        await websocket.send_json({"type": "error", "message": f"Unknown event type: {event_type}"})


@router.websocket("/api/chat/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    user = await _authenticate_ws(token)
    if not user or user.get("role") not in ["seeker", "employer"]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = str(user["_id"])
    await connection_manager.connect(user_id, websocket)

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                await _handle_event(user, user_id, raw, websocket)
            except HTTPException as e:
                # 🎯 Error ដែលមានន័យ (ឧ. 403 Not a participant, 404 Not found) - ជូនដំណឹងទៅ Client
                # ដោយមិនកាត់ផ្តាច់ Connection (User នៅតែអាចបន្ត Chat លើ Conversation ផ្សេងទៀត)
                await websocket.send_json({"type": "error", "message": e.detail})
            except Exception as e:
                print(f"[Chat WebSocket Handler Error] user={user_id} error={e}")
                await websocket.send_json({"type": "error", "message": "Something went wrong. Please try again."})

    except WebSocketDisconnect:
        connection_manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"[Chat WebSocket Fatal Error] user={user_id} error={e}")
        connection_manager.disconnect(user_id, websocket)
