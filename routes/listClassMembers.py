
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import  HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from authentication.authentication import auth_required
from models.database import ClassSubject, Student, Teacher, TeacherClass, User, get_db
from fastapi.templating import Jinja2Templates
from utils.utils import get_initials,random_color

router = APIRouter()

templates = Jinja2Templates(directory="templates")

templates.env.filters['initials'] = get_initials

templates.env.filters["random_color"] = random_color

@router.post("/classroom_students", response_class=HTMLResponse)
async def showClassMembers(request: Request, subject_id: str = Form(...), subject: str = Form(...), class_id: str = Form(...), db: Session = Depends(get_db)
                           ,is_auth= Depends(auth_required)):

    try:
        # Query students using SQLAlchemy
        students = (
            db.query(User.full_name)
            .join(Student, User.user_id == Student.user_id)
            .join(ClassSubject, Student.class_id == ClassSubject.class_id)
            .filter(User.role == "student")
            .filter(Student.class_id == class_id)
            .filter(ClassSubject.subject_id == subject_id)
            .all()
        )
        
        # Transform SQLAlchemy result into a list of names
        students = [(student.full_name,) for student in students]


        teacher_name = (
            db.query(User.full_name)
            .join(Teacher, Teacher.user_id == User.user_id)
            .join(TeacherClass, TeacherClass.teacher_id == Teacher.teacher_id)
            .filter(TeacherClass.class_id == class_id, TeacherClass.subject_id == subject_id)
            .first()
        )

        teacher_name = teacher_name[0] if teacher_name else "Teacher Not Assigned"
        
        return templates.TemplateResponse("list_of_students.html", {
            "request": request,
            "listofstu": students,
            "subject_name": subject,
            "class_id": class_id,
            "subject_id": subject_id,
            "subject": subject,
            "teacher": teacher_name
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)


