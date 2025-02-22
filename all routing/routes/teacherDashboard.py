from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from models.database import Classroom, Message, Subject, Teacher, TeacherClass 
from models.database import get_db
from fastapi.templating import Jinja2Templates
from sqlalchemy import func

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, search: str = None, db: Session = Depends(get_db)):
    current_teacher = request.session.get('user_name')
    current_user_id = request.session.get('user_id')

    try:
        # Query teaching modules using SQLAlchemy
        teaching_modules = (
            db.query(
                Teacher.user_id,
                Teacher.teacher_id,
                TeacherClass.class_id,
                Classroom.class_name,
                TeacherClass.subject_id,
                Subject.subject_name
            )
            .join(TeacherClass, Teacher.teacher_id == TeacherClass.teacher_id)
            .join(Classroom, TeacherClass.class_id == Classroom.class_id)
            .join(Subject, TeacherClass.subject_id == Subject.subject_id)
            .filter(Teacher.user_id == current_user_id)
            .order_by(TeacherClass.class_id.asc())
            .all()
        )

        inbox_messages = db.query(
                func.count().label('total_unread')
            ).filter(
                Message.receiver_id == current_user_id,  # filter for receiver_id 4
                Message.status == 'unread'  # filter for unread status
            ).scalar() 

        if search:
            teaching_modules=[record for record in teaching_modules if record[3].lower() == search.lower()]

        # Render the teacher dashboard template
        return templates.TemplateResponse(
            "Teacher/teacher_landingpage.html",
            {
                "request": request,
                "teaching_modules": teaching_modules,
                "current_teacher": current_teacher,  
                "inbox_message": inbox_messages
            },
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

