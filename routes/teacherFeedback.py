from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from services.AIServices.Sentiment import SentimentAnalyzer
import os
from models.database import Classroom, FeedBack, Student, Teacher, User, get_db
from authentication.authorizations import studentAllowed
from authentication.authentication import auth_required
from sqlalchemy import select, func

router = APIRouter()

templates = Jinja2Templates(directory="templates")

MODEL_DIR = "static\sentimentModel\checkpoint-1500"

@router.get("/")
async def feedback_teacher(request: Request,db: Session = Depends(get_db), send:str = None,  is_auth= Depends(auth_required),
    is_allowed= Depends(studentAllowed)):

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
    mssg: str = Form(...),
    is_auth= Depends(auth_required),
    is_allowed= Depends(studentAllowed),
):
    try:

        setiment_model = SentimentAnalyzer(MODEL_DIR)

        sentiment = setiment_model.predict(mssg)

        predicted_label = sentiment['predicted_label']
        confidence_score = sentiment['confidence_score']

        # Concatenate them into a single string
        sentiment_result = f"{predicted_label} ({confidence_score}%)"

        
        feedback_query = db.query(FeedBack).filter(
        FeedBack.student == 'miraj deepbhandari',
        func.date(FeedBack.date) == func.curdate()
    ).all()
        # if results:
        #     request.session["error"] = "You have already submitted feedback today!"
        #     return RedirectResponse(url="/", status_code=303)

        new_feedback = FeedBack(
            teacher=choosed_teacher,
            subject=subject,
            student= request.session['user_name'],
            classroom=classroom,
            message=mssg,
            feedback_score=sentiment_result
        )

        db.add(new_feedback)
        db.commit()

        return RedirectResponse(url="/feedbackform?send=success", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")  # Ideally, replace this with logging
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)




 

   



