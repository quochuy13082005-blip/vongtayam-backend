from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        import json
        for conn in list(self.active):
            try:
                await conn.send_text(json.dumps(message))
            except:
                self.disconnect(conn)

manager = ConnectionManager()

