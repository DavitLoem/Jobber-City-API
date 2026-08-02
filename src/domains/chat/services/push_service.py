import os
import json
from typing import Optional

import firebase_admin
from firebase_admin import credentials, messaging

_firebase_app = None


def _get_firebase_app():
    """
    Lazy-init Firebase Admin SDK (មិន Init ស្វ័យប្រវត្តិពេល Import ទេ ដើម្បីកុំឱ្យ App
    Crash ពេល Local Dev មិនទាន់មាន Firebase Credentials)។

    គាំទ្រ ២ របៀបផ្តល់ Credentials៖
    1. FIREBASE_CREDENTIALS_JSON - ដាក់ខ្លឹមសារ JSON ទាំងមូលរបស់ Service Account ជា
       Environment Variable តែមួយបន្ទាត់ (ងាយសម្រាប់ Deploy លើ Render/Railway ដែល
       មិនងាយ Upload File ដាច់ដោយឡែក)។
    2. FIREBASE_CREDENTIALS_PATH - Path ទៅកាន់ File serviceAccountKey.json នៅលើ
       Disk (ងាយសម្រាប់ Local Development)។
    """
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if firebase_admin._apps:
        _firebase_app = firebase_admin.get_app()
        return _firebase_app

    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    elif cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        # 🎯 គ្មាន Credentials ទេ = រំលង Push ដោយស្ងាត់ៗ (Real-time WebSocket នៅតែដំណើរការធម្មតា)
        # ល្អសម្រាប់ Local Development មុនចង់ Setup Firebase Project ពិតប្រាកដ
        return None

    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


async def send_chat_push_notification(
    fcm_tokens: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> dict:
    """
    ផ្ញើ Push Notification ទៅ Device Token មួយ ឬច្រើនក្នុងពេលតែមួយ (Multicast)។

    ត្រូវហៅមុខងារនេះតែពេលអ្នកទទួល "មិន Online" លើ WebSocket ប៉ុណ្ណោះ (មើល
    chat_service.send_message) — មិនចាំបាច់ផ្ញើ Push ស្ទួនពេលគាត់កំពុងបើក Chat
    រួចទទួល Message តាម WebSocket រួចរាល់ទៅហើយ។
    """
    app = _get_firebase_app()
    if not app or not fcm_tokens:
        return {"sent": 0, "failed": 0, "skipped": True}

    string_data = {k: str(v) for k, v in (data or {}).items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=string_data,
        tokens=fcm_tokens,
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)

        # 🎯 លុប Token ណាដែល Invalid ចោល (App ត្រូវបានលុប/Uninstall, Token ចាស់ផុតកំណត់)
        # ដើម្បីកុំឱ្យបន្ត Retry ខាតពេល ហើយកុំឱ្យ Firebase Quota ខាតទៅឥតប្រយោជន៍
        invalid_tokens = [
            fcm_tokens[i] for i, r in enumerate(response.responses) if not r.success
        ]

        return {
            "sent": response.success_count,
            "failed": response.failure_count,
            "invalid_tokens": invalid_tokens,
        }
    except Exception as e:
        print(f"[Push Notification Error] {e}")
        return {"sent": 0, "failed": len(fcm_tokens), "error": str(e)}
