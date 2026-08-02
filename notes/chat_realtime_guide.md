# Real-time Chat (Seeker ↔ Employer) — Architecture & Integration Guide

Backend implementation lives under `src/domains/chat/`. This doc explains the design decisions,
the algorithms behind them, the API/WebSocket protocol, and how to wire it up from the Flutter app.
Ready-to-copy Flutter client code is in `flutter_chat_kit/`.

## 1. What was chosen, and why

Three decisions were made with you before building:

1. **Transport: native FastAPI WebSockets** — no external chat service (Pusher/Ably) and no
   Firebase Firestore. Zero extra cost, messages live in your existing MongoDB, full control.
2. **Push notifications: Firebase Cloud Messaging (FCM)** — the only external service used, and
   only for waking up the app when it's closed/backgrounded. Free, and the Flutter standard.
3. **Single server instance for now** — connections are tracked in-memory. The code is written so
   this can be swapped for Redis pub/sub later without changing any calling code (see §7).

## 2. Data model (MongoDB)

**`conversations`** — one thread per (seeker, employer) pair, not per job:

```
{
  _id, seeker_id, employer_id, job_id (optional, first job discussed),
  participant_ids: [seeker_id, employer_id],   # used for the "my chat list" query
  last_message, last_message_type, last_message_at, last_sender_id,
  unread_count: { "<user_id>": 0, "<user_id>": 2 },   # denormalized, O(1) read
  last_read_at: { "<user_id>": <datetime|null> },      # drives "Seen" ticks
  created_at, updated_at
}
```

**`chat_messages`**:

```
{ _id, conversation_id, sender_id, sender_role, message_type, content,
  attachment_url, status, client_temp_id, created_at }
```

**`device_tokens`** — FCM tokens per device, keyed by token (not by user, since the same phone can
log in as different accounts):

```
{ _id, user_id, fcm_token, platform, created_at, updated_at }
```

Indexes are created automatically on server startup (see `create_chat_indexes` in `main.py`).

## 3. Algorithms

**Get-or-create conversation.** A seeker and an employer only ever get one thread. Starting a chat
from a job post, an applicant card, or a company profile all resolve to the same conversation —
`job_id` is stored just as display context the first time, not as part of the lookup key. This
avoids fragmenting chat history the way per-job threads would.

**Write-then-broadcast message flow.** On send: (1) persist to MongoDB first — the DB is the
source of truth, so a message is never lost even if the live broadcast step fails; (2) increment
the recipient's `unread_count` and update the conversation's last-message summary with a single
atomic `$inc`/`$set`; (3) push the message over WebSocket to every connection the sender has open
(multi-device sync) and every connection the recipient has open; (4) if the recipient had zero
active connections, fall back to an FCM push instead.

**Connection manager (multi-device fan-out).** `user_id -> Set[WebSocket]` in memory. A user can be
logged in on a phone and tablet simultaneously and both get every event. `is_online(user_id)` is
what decides whether step 4 above (push notification) is needed at all — no push is sent to a user
who's actively looking at the chat.

**Cursor-based pagination**, not `skip/limit`. History is paged with `?before=<message_id>` — Mongo
`ObjectId`s encode their creation time, so `{_id: {$lt: ObjectId(before)}}` sorted descending is a
correct and index-friendly "give me older messages" query that stays fast no matter how long the
chat history grows, unlike `.skip(n)` which gets slower the deeper you page.

**Unread counts + read receipts without rewriting every message row.** Rather than updating a
`read` flag on every historical message (expensive at scale), each conversation stores a single
`last_read_at[user_id]` timestamp and a denormalized `unread_count[user_id]` integer. Marking a
conversation read is one `$set` update, O(1) regardless of history length, and emits a
`read_receipt` event so the sender's UI can flip single-tick → double-tick live.

**Typing indicator.** Not persisted — it's a pure ephemeral WebSocket relay to whichever device the
other participant has open, dropped silently if they're offline.

**FCM token hygiene.** When a push send comes back with per-token failures (uninstalled app,
expired token), those tokens are deleted from `device_tokens` immediately, so you don't keep paying
the round-trip cost of pushing to dead devices.

## 4. REST API reference

All routes require `Authorization: Bearer <access_token>` and are restricted to `seeker`/`employer`
roles (`require_mobile_users`).

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat/conversations` | Get-or-create a thread. Body: `{ other_user_id, job_id? }` |
| GET | `/api/chat/conversations?page=&limit=` | List my threads, newest first |
| GET | `/api/chat/conversations/{id}/messages?before=&limit=` | Paginated history |
| POST | `/api/chat/conversations/{id}/read` | Mark thread read, emits read receipt |
| POST | `/api/chat/conversations/{id}/messages` | Send via REST (fallback when not on WS) |
| POST | `/api/chat/device-tokens` | Register FCM token. Body: `{ fcm_token, platform }` |
| DELETE | `/api/chat/device-tokens` | Remove token (call on logout) |

All responses use the existing `APIResponse` envelope (`{ success, message, data }`).

## 5. WebSocket protocol

Connect to: `wss://<your-host>/api/chat/ws?token=<access_token>`

The JWT is passed as a query param, not a header — WebSocket handshakes can't reliably carry
custom headers across all clients/proxies, so this matches your existing `verify_token()` logic
but over the query string. **Always use `wss://` in production** so the token isn't exposed on the
wire.

**Client → Server**

```jsonc
{ "type": "send_message", "conversation_id": "...", "content": "...", "message_type": "text", "client_temp_id": "uuid-optional" }
{ "type": "typing", "conversation_id": "...", "is_typing": true }
{ "type": "read", "conversation_id": "..." }
{ "type": "ping" }
```

**Server → Client**

```jsonc
{ "type": "new_message", "data": { id, conversation_id, sender_id, sender_role, message_type, content, attachment_url, status, client_temp_id, created_at } }
{ "type": "typing", "conversation_id": "...", "user_id": "...", "is_typing": true }
{ "type": "read_receipt", "conversation_id": "...", "reader_id": "...", "read_at": "..." }
{ "type": "error", "message": "..." }
{ "type": "pong" }
```

`client_temp_id` is a UUID your Flutter app generates before the server has assigned a real
message `_id`. Show the message immediately (optimistic UI), then when `new_message` comes back
with the same `client_temp_id`, swap the temporary bubble for the confirmed one.

## 6. Firebase setup (push notifications only — chat itself needs no Firebase)

1. Create a project at https://console.firebase.google.com (free).
2. Add your Android app (package name) and iOS app (bundle id); download
   `google-services.json` / `GoogleService-Info.plist` into the Flutter project as usual.
3. Project Settings → Service Accounts → **Generate new private key** → downloads a JSON file.
4. On the backend, set **one** of:
   - `FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json` (local dev), or
   - `FIREBASE_CREDENTIALS_JSON='{...file contents as one line...}'` (hosting platforms without
     file uploads, e.g. Render/Railway).
5. That's it — `firebase-admin` was added to `requirements.txt`. If neither var is set, push sends
   are silently skipped (WebSocket chat still works fully; you just won't get background alerts).

## 7. Scaling later (not needed now)

Everything above assumes one server process. If you later run multiple instances behind a load
balancer, a user's two WebSocket connections could land on different instances, and
`ConnectionManager.send_to_user` would only see the one on its own process. The fix is to replace
the in-memory `dict` in `connection_manager.py` with Redis pub/sub (each instance subscribes to a
channel per connected user, publishes there on broadcast) — the `connect/disconnect/send_to_user/
is_online` method signatures were kept deliberately simple so this swap doesn't touch any other
file.

## 8. Flutter integration

See `flutter_chat_kit/` for ready-to-copy Dart files and `flutter_chat_kit/README.md` for the
package list and wiring steps.
