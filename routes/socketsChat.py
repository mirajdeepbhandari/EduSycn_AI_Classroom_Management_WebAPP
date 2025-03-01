from typing import List
from authentication.authentication import auth_required
from services.WebSockets.ChatManager import ConnectionManager
from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.database import get_db
from models.database import Chatroom, Message

router = APIRouter()

manager = ConnectionManager()

@router.websocket("/ws/{chat_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_id: int,  # Changed to int to match your schema
    user_id: int,  # Changed to int to match your schema
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required)
):
    await manager.connect(websocket, str(chat_id), str(user_id))
    try:
        while True:
            data = await websocket.receive_json()
            
            # Get chatroom to determine receiver_id
            chatroom = db.query(Chatroom).filter(Chatroom.chat_id == chat_id).first()
            receiver_id = chatroom.user2_id if user_id == chatroom.user1_id else chatroom.user1_id
            
            # Create new message
            message = Message(
                content=data["message"],
                chat_id=chat_id,
                sender_id=user_id,
                receiver_id=receiver_id,
                timestamp=func.now(),
            )
            db.add(message)
            db.flush()  # Get the message ID without committing
            
            # Prepare message data
            message_data = {
                "msg_id": message.msg_id,
                "content": message.content,
                "sender_id": user_id,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
            
            # Try to deliver the message
            await manager.send_message(message_data, str(chat_id), str(user_id))
            
            db.commit()
            
    except WebSocketDisconnect:
        manager.disconnect(str(chat_id), str(user_id))




@router.get("/api/messages/{chat_id}")
async def get_messages(
    chat_id: int,
    db: Session = Depends(get_db), is_auth= Depends(auth_required)
):
    try:
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.timestamp)
            .all()
        )
        
        return [
            {
                "msg_id": msg.msg_id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    

class ActiveUsersResponse(BaseModel):
    active_users: List[str]
    total_users: int

@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_active_users(is_auth= Depends(auth_required)):
    """
    Returns a list of all active user IDs across all chats.
    Returns:
        {
            "active_users": ["user1", "user2", "user3"],
            "total_users": 3
        }
    """
    try:
        # Get unique user IDs from all chats
        unique_users = set()
        for chat_users in manager.active_connections.values():
            unique_users.update(chat_users.keys())
            
        return ActiveUsersResponse(
            active_users=list(unique_users),
            total_users=len(unique_users)
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch active users: {str(e)}"
        )
