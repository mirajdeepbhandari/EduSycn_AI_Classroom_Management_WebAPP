from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from authentication.authentication import auth_required
from authentication.authorizations import studentAllowed
from models.database import get_db, Student, Classroom, ClassSubject, Subject, Message
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")




@router.get("/", response_class=HTMLResponse)
async def student_dashboard(request: Request, search_query: str = None, db: Session = Depends(get_db),
                             is_auth= Depends(auth_required), is_allowed= Depends(studentAllowed)):
    user_id = request.session.get('user_id')
    user = request.session.get('user_name')
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    try:
        # Query the necessary data using SQLAlchemy
        student_data = (
            db.query(Student.student_id, Student.user_id, Student.class_id, Classroom.class_name,
                     Subject.subject_name, Subject.subject_id)
            .join(Classroom, Classroom.class_id == Student.class_id)
            .join(ClassSubject, ClassSubject.class_id == Student.class_id)
            .join(Subject, Subject.subject_id == ClassSubject.subject_id)
            .filter(Student.user_id == user_id)
            .all()
        )

        student_counts = (
            db.query(
                ClassSubject.class_id,
                ClassSubject.subject_id,
                func.count(Student.student_id).label("total_students")
            )
            .join(Student, Student.class_id == ClassSubject.class_id)
            .group_by(ClassSubject.class_id, ClassSubject.subject_id)
            .order_by(ClassSubject.class_id, ClassSubject.subject_id)
            .all()
        )

        inbox_messages = db.query(
                func.count().label('total_unread')
            ).filter(
                Message.receiver_id == user_id,  # filter for receiver_id 4
                Message.status == 'unread'  # filter for unread status
            ).scalar() 
        
        is_notifyread = db.query(Student.is_notifyread).filter(Student.user_id == user_id).first()
        
        if student_data:

            for i in range(len(student_data)):
                # Get the 2nd and last values from student_data
                student_data_second = student_data[i][2]
                student_data_last = student_data[i][-1]

                # Compare with the 1st and 2nd values of student_counts
                for item in student_counts:
                    if item[0] == student_data_second and item[1] == student_data_last:
                        # If they match, convert student_data[i] to a list and append the 3rd value from student_counts
                        student_data_list = list(student_data[i])  # Convert to list
                        student_data_list.append(item[2])  # Append total_students
                        student_data[i] = tuple(student_data_list)  # Convert back to tuple

            class_id = student_data[0][2]
            class_name = student_data[0][3]
            # Group subjects and subject_ids
            subjects = [subject[4] for subject in student_data]
            subject_ids = [subject[5] for subject in student_data]
            noofstudents = [subject[6] for subject in student_data]
            subject_data = list(zip(subjects, subject_ids, noofstudents))
            
            # Search Classroom Functionality
            if search_query:
                subject_data = [record for record in subject_data if record[0].lower() == search_query.lower()]

            return templates.TemplateResponse("student_page.html", {
                "request": request,
                "subject_data": subject_data,
                "class_name": class_name,
                "class_id": class_id,
                "name": user,
                "inbox_message": inbox_messages,
                "is_Notifyread": is_notifyread[0],
                "userId": user_id
            })

        else:
            # If no data is found for the student, redirect
            request.session["error"] = "Please Contact the Admin! for ID Setup"
            return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
