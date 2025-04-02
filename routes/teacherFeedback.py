from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from models.database import Classroom, Student, Teacher, User, get_db


router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/")
async def feedback_teacher(request: Request,db: Session = Depends(get_db)):

    result = (
        db.query(Teacher.teacher_id, User.full_name.label("teacher_name"))
        .join(User, Teacher.user_id == User.user_id)
        .filter(User.role == "teacher")
        .all()
    )

    classroom_id = db.query(Student.class_id).filter(Student.user_id == request.session.get('user_id')).first()


    classroom = db.query(Classroom.class_name).filter(Classroom.class_id == classroom_id[0]).first()


    return templates.TemplateResponse("feedback.html", {"request": request, "teachers":result, "classroom": classroom[0]})



