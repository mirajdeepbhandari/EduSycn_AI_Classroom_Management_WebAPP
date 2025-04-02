from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from models.database import Classroom, FeedBack, Student, Teacher, User, get_db


router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/")
async def feedback_teacher(request: Request,db: Session = Depends(get_db), send:str = None):

    result = (
        db.query(Teacher.teacher_id, User.full_name.label("teacher_name"))
        .join(User, Teacher.user_id == User.user_id)
        .filter(User.role == "teacher")
        .all()
    )

    classroom_id = db.query(Student.class_id).filter(Student.user_id == request.session.get('user_id')).first()

    classroom = db.query(Classroom.class_name).filter(Classroom.class_id == classroom_id[0]).first()

    return templates.TemplateResponse("feedback.html", {"request": request, "teachers":result, "classroom": classroom[0],
                                                      "send": send})



@router.post("/")
async def feedback_teacher(
    request: Request,
    db: Session = Depends(get_db),
    choosed_teacher: str = Form(...), 
    subject: str = Form(...), 
    classroom: str = Form(...),
    mssg: str = Form(...)
):
    try:
        new_feedback = FeedBack(
            teacher=choosed_teacher,
            subject=subject,
            classroom=classroom,
            message=mssg,
            feedback_score="nea"
        )

        db.add(new_feedback)
        db.commit()

        return RedirectResponse(url="/feedbackform?send=success", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")  # Ideally, replace this with logging
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)




 

   



