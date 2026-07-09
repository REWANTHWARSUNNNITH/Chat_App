from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id -> websocket (one active connection per user)
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    def online_user_ids(self):
        return list(self.active_connections.keys())

    async def send_to_user(self, user_id: int, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast_all(self, message: dict):
        for ws in self.active_connections.values():
            await ws.send_json(message)


manager = ConnectionManager()