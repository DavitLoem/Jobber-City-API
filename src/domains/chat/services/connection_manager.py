from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    គ្រប់គ្រង WebSocket Connections ទាំងអស់ដែលកំពុង Active នៅលើ Server Instance នេះ។

    🎯 រចនាសម្ព័ន្ធទិន្នន័យ៖ user_id (str) -> Set[WebSocket]
    ការប្រើ Set ជំនួសឱ្យ WebSocket តែមួយ អនុញ្ញាតឱ្យ User ម្នាក់ Login ច្រើន Device
    ក្នុងពេលតែមួយ (ទូរស័ព្ទ + Tablet) ដោយគ្រប់ Device ទាំងអស់ទទួលបាន Message ដូចគ្នា
    (Multi-device Sync)។

    ចំណាំសម្រាប់ការពង្រីកនាពេលអនាគត (Horizontal Scaling)៖
    ដ្យាក់ក្រាមនេះសម្រាប់ដំណើរការជាមួយ Server តែមួយ Instance ប៉ុណ្ណោះ។ ប្រសិនបើអនាគត
    Deploy ច្រើន Instance ក្រោយ Load Balancer, Dictionary នេះនឹងឃើញតែ User ដែល
    Connect មក Instance ជាក់លាក់នេះប៉ុណ្ណោះ (User ២ នាក់ Connect ខុស Instance គ្នា
    នឹងមិនឃើញគ្នា)។ ដំណោះស្រាយគឺប្តូរ Class នេះឱ្យប្រើ Redis Pub/Sub instead
    (រាល់ Instance Subscribe Channel ផ្ទាល់ខ្លួន ហើយ Publish ពេល Broadcast) ដោយមិន
    ចាំបាច់ប្តូរ Interface ខាងក្រៅ (connect / disconnect / send_to_user / is_online)
    ដែលនៅតែដដែល — Service ដទៃទៀតទាំងអស់ហៅតាម Interface នេះ មិនចាំបាច់ដឹងពី
    Implementation ខាងក្នុងសោះ។
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        connections = self.active_connections.get(user_id)
        if connections and websocket in connections:
            connections.discard(websocket)
            if not connections:
                self.active_connections.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return bool(self.active_connections.get(user_id))

    async def send_to_user(self, user_id: str, payload: dict) -> bool:
        """
        ផ្ញើ Event ទៅគ្រប់ Device ទាំងអស់របស់ User នេះដែលកំពុង Online។
        ត្រឡប់ True ប្រសិនបើមាន Device យ៉ាងហោចណាស់មួយទទួលបាន (មានន័យថា
        មិនចាំបាច់ផ្ញើ Push Notification ទៀតទេ)។
        """
        connections = self.active_connections.get(user_id)
        if not connections:
            return False

        dead_sockets = []
        for ws in connections:
            try:
                await ws.send_json(payload)
            except (WebSocketDisconnect, RuntimeError, ConnectionError, OSError) as e:
                # 🎯 Error ទាំងនេះមានន័យថា Connection ពិតជាបាត់ (Client បិទ App/Network ដាច់ភ្លាមៗ)
                # ទើបសមហេតុផលក្នុងការដក Connection នេះចេញពី Registry
                print(f"[ConnectionManager] Dropping dead connection for user={user_id}: {e}")
                dead_sockets.append(ws)
            except Exception as e:
                # 🎯 កំហុសផ្សេងទៀត (ឧ. Payload មិនអាច Serialize បាន) មិនមែនមកពី Connection ខូចទេ
                # កុំដក Connection ចេញ ព្រោះវានៅតែ Active — គ្រាន់តែ Log ឱ្យឃើញភ្លាមៗ (កុំស្ងាត់ស្ងៀម
                # ដូចមុន ព្រោះនោះជាមូលហេតុដែល Bug នេះលាក់កំបាំងអស់រយៈពេលមួយ)
                print(f"[ConnectionManager] send_json error (connection kept alive) for user={user_id}: {e}")

        for ws in dead_sockets:
            connections.discard(ws)

        return len(connections) > 0


# 🎯 Singleton តែមួយ ប្រើរួមគ្នាទូទាំង App (Import object នេះទៅប្រើនៅកន្លែងផ្សេងទៀត)
connection_manager = ConnectionManager()
