from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import teacher_student_Allowed
from models.database import Chatroom, User
from models.database import get_db
from models.database import Message, User
from fastapi.templating import Jinja2Templates
from sqlalchemy import func

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/inbox", response_class=HTMLResponse)
async def inbox(
    request: Request,
    searched_user: str = None,
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required),
    is_allowed= Depends(teacher_student_Allowed)
):
    current_role = request.session.get("role")
    me = request.session.get('user_id')
    
    try:
        all_users_query = (
            db.query(
                User.user_id,
                User.full_name
            )
            .filter(User.user_id != me)
        )
        
        if searched_user:
            all_users_query = all_users_query.filter(
                User.full_name.ilike(f"%{searched_user}%")
            )
        
        all_users = all_users_query.all()

        all_unread_counts = (
            db.query(
                Message.sender_id,
                Message.receiver_id,
                func.count().label('total_unread')
            )
            .filter(
                Message.receiver_id == me,
                Message.status == 'unread'
            )
            .group_by(
                Message.sender_id,
                Message.receiver_id
            )
            .all()
        )
        
        unread_count_dict = {str(row.sender_id): row.total_unread for row in all_unread_counts}

        return templates.TemplateResponse(
            "feeds.html",
            {
                "request": request,
                "current_role": current_role,
                "allusers": all_users,
                "unread_counts": unread_count_dict
            }
        )
  
    except Exception as e:
        print(f"An error occurred in inbox: {e}")
        request.session["error"] = "Something Went Wrong on Server!"
        return RedirectResponse(url="/", status_code=303)
 
@router.get("/chatListings", response_class=HTMLResponse)
async def Listings(request: Request,
                   user_id: str,
                   user_name: str,
                   db: Session = Depends(get_db),
                   is_auth= Depends(auth_required),
                   is_allowed= Depends(teacher_student_Allowed)):
    
    try:
        me = request.session.get('user_id')

        # Check if a chatroom already exists between user1 (me) and user2
        existing_chatroom = db.query(Chatroom).filter(
            (Chatroom.user1_id == me) & (Chatroom.user2_id == user_id) |
            (Chatroom.user1_id == user_id) & (Chatroom.user2_id == me)
        ).first()


        if existing_chatroom:
            # If the chatroom exists, return the existing chatroom details
            chatroom = existing_chatroom

            db.query(Message).filter(
            (Message.chat_id == chatroom.chat_id) & (Message.receiver_id == me)).update({"status": "read"})

            db.commit()
            db.refresh(chatroom)

        else:
            # Create a new chatroom if it doesn't exist
            chatroom = Chatroom(
                user1_id=me,
                user2_id=user_id,
                created_date=datetime.now(timezone.utc)
            )
            db.add(chatroom)
            db.commit()
            db.refresh(chatroom)

        user2_name = db.query(User.full_name).filter(User.user_id == user_id).first()

        # Render the chatroom details in the template
        return templates.TemplateResponse(
            "listings.html",
            {   "request": request,
                "chatroom_id": chatroom.chat_id,
                "user2_name": user2_name[0],
                "user1_id": me,
                "user2_id": user_id,
            }
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)


@router.get("/get_unread_counts", response_class=JSONResponse)
async def get_unread_counts(request: Request, db: Session = Depends(get_db),
                            is_auth= Depends(auth_required), is_allowed= Depends(teacher_student_Allowed)):
    # Get the current logged-in user ID from the session
    me = request.session.get('user_id')

    try:
        unread_message_counts = (
            db.query(
                Message.sender_id,
                Message.receiver_id,
                func.count().label('total_unread')
            )
            .filter(
                Message.receiver_id == me,
                Message.status == 'unread'
            )
            .group_by(
                Message.sender_id,
                Message.receiver_id
            )
            .all()
        )
        
        unread_count_dict = {row.sender_id: row.total_unread for row in unread_message_counts}
        
        return unread_count_dict
    except Exception as e:
        return {"error": str(e)}

