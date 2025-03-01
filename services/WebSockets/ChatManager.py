from typing import Dict, List

from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store active connections: {chat_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str, user_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}
        self.active_connections[chat_id][user_id] = websocket

    def disconnect(self, chat_id: str, user_id: str):
        if chat_id in self.active_connections:
            if user_id in self.active_connections[chat_id]:
                del self.active_connections[chat_id][user_id]
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def send_message(self, message: dict, chat_id: str, sender_id: str):
        if chat_id in self.active_connections:
            # Send to all users in the chat except sender
            for user_id, connection in self.active_connections[chat_id].items():
                if user_id != sender_id:
                    await connection.send_json(message)
                    return True  
        return False  


