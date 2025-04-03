import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from authentication.authentication import auth_required
from authentication.authorizations import adminAllowed
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models.database import  FeedBack,Classroom, get_db

load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def seekFeedback(request: Request,
                       is_auth= Depends(auth_required),
                       db: Session = Depends(get_db)
                       ,is_allowed= Depends(adminAllowed)):

    feedbacks = db.query(FeedBack.id, FeedBack.teacher, FeedBack.student, FeedBack.classroom,
     FeedBack.date, FeedBack.feedback_score, FeedBack.message, FeedBack.subject).all()
    
    class_names = db.query(Classroom.class_name).all()
    class_names = [name[0] for name in class_names]
    print(class_names)

    
    return templates.TemplateResponse("SUPERADMIN/SeeFeedback.html", {"request": request, "feedbacks": feedbacks,
     "class_names": class_names})