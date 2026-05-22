from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, scan_id: str, websocket: WebSocket):
        await websocket.accept()

        self.active_connections[scan_id] = websocket

    def disconnect(self, scan_id: str):
        if scan_id in self.active_connections:
            del self.active_connections[scan_id]

    async def send_message(self, scan_id: str, data: dict):
        websocket = self.active_connections.get(scan_id)

        if websocket:
            await websocket.send_json(data)


manager = ConnectionManager()