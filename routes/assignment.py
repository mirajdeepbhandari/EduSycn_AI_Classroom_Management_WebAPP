from datetime import datetime
import os
import shutil
from fastapi import APIRouter, Form, Request, Depends, UploadFile
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import studentAllowed, teacherAllowed
from models.database import Assignment, Notification, Student,Submission, Teacher, User 
from models.database import get_db
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from utils.utils import format_datetime
from utils.utils import format_datetime,get_initials,random_color, get_filename

router = APIRouter()

templates = Jinja2Templates(directory="templates")

templates.env.filters['initials'] = get_initials

templates.env.filters["random_color"] = random_color

templates.env.filters['getpostname'] = get_filename

@router.post("/give_assignment", response_class=HTMLResponse)
async def giveAssignment(
    request: Request,
    subject_id: str = Form(...),
    class_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(None),
    teacher_id: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None),
    assignment_file: UploadFile = Form(None),
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required),
    is_allowed= Depends(teacherAllowed),
):
    if title and description and due_date:
        save_location = None

        if assignment_file:
            uploads_base = "static/TeacherAssignment"

            # Create the full path for the file save location
            save_location = os.path.join(uploads_base, class_id, subject_id, subject, assignment_file.filename)

            # Check if the directory exists and if it contains any files
            directory = os.path.dirname(save_location)
            if os.path.exists(directory):
                # If the directory exists, remove all files in the directory
                shutil.rmtree(directory)  # Remove the entire directory and its contents

            # Ensure the directory exists
            os.makedirs(directory, exist_ok=True)

            # Save the uploaded file
            with open(save_location, "wb") as file_object:
                shutil.copyfileobj(assignment_file.file, file_object)

        try:
            # Fetch teacher_id using SQLAlchemy
            teacher = db.query(Teacher).filter(Teacher.user_id == teacher_id).first()

            save_location = save_location.replace('static/', '')

            # Create a new assignment record using SQLAlchemy ORM
            new_assignment = Assignment(
                teacher_id=teacher.teacher_id,
                class_id=class_id,
                subject_id=subject_id,
                assignment_title=title,
                assignment_description=description,
                due_date=datetime.strptime(due_date, "%Y-%m-%d") if due_date else None,
                link=save_location
            )

            # Add and commit the new assignment to the database
            db.add(new_assignment)
            db.commit()

            assignment_notification=Notification(
              content = f"A new assignment has been created for {subject}. Make sure to submit the assignment on time.",
                date=datetime.now(),
                which_class=class_id
            )

            db.add(assignment_notification)
            db.commit()

            db.query(Student).filter(Student.class_id == class_id).update({"is_notifyread": "no"})

            # Delete older assignments with the same class_id and subject_id
            db.query(Assignment).filter(
                Assignment.class_id == class_id,
                Assignment.subject_id == subject_id,
                Assignment.created_at < db.query(func.max(Assignment.created_at)).filter(
                    Assignment.class_id == class_id,
                    Assignment.subject_id == subject_id
                )
            ).delete()
            db.commit()


            # Handle assignment creation logic here
            return templates.TemplateResponse(
                "TEACHER/give_assignment.html",
                {
                    "request": request,
                    "subject_id": subject_id,
                    "class_id": class_id,
                    "subject_name": subject,
                    "message": "Assignment created successfully",
                    "teacher_id": teacher_id
                }
            )

        except Exception as e:
                    print(f"An error occurred: {e}")
                    db.rollback()  # Rollback in case of an error
                    request.session["error"] = "Something Went Wrong on Server !!!"
                    return RedirectResponse(url="/", status_code=303)
    else:
        # Render the assignment form if required fields are missing
        return templates.TemplateResponse(
            "TEACHER/give_assignment.html",
            {
                "request": request,
                "subject_id": subject_id,
                "class_id": class_id,
                "subject_name": subject,
                "teacher_id": teacher_id
            },
        )




@router.post("/assignmentview", response_class=HTMLResponse)
async def viewAssignment(request: Request, subject_id: str = Form(...), class_id: str = Form(...),
                          subject:str = Form(...), teacher_id: str = Form(...), is_auth= Depends(auth_required)
                          , is_allowed= Depends(teacherAllowed)):
    return templates.TemplateResponse("Teacher/inside_assignment.html", {"request": request,
                                                            "subject_id": subject_id,
                                                            "class_id": class_id,
                                                            "subject_name": subject,
                                                            "teacher_id": teacher_id})



@router.post("/studentReportView", response_class=HTMLResponse)
async def studentMarkReport(request: Request, subject_id: str = Form(...), 
                            class_id: str = Form(...), subject: str = Form(...),
                            teacher_id: str = Form(...), db: Session = Depends(get_db), is_auth= Depends(auth_required)
                            , is_allowed= Depends(teacherAllowed)):

    try:
        # Query for students who have submitted the assignment
        submitted_students_query = (
            db.query(
                User.full_name,
                Submission.submission_date,
                Submission.file_path,
                Assignment.assignment_title
            )
            .join(Submission, Submission.assignment_id == Assignment.assignment_id)
            .join(Student, Submission.student_id == Student.student_id)
            .join(User, Student.user_id == User.user_id)
            .filter(Student.class_id == class_id, Assignment.subject_id == subject_id)
            .all()
        )

        if submitted_students_query:
            students_who_submitted = [row[0] for row in submitted_students_query]

            # Query for all students enrolled in the class
            all_students_enrolled_query = (
                db.query(User.full_name)
                .join(Student, Student.user_id == User.user_id)
                .join(Assignment, Assignment.class_id == Student.class_id)
                .filter(Student.class_id == class_id, Assignment.subject_id == subject_id)
                .distinct()
                .all()
            )

            all_students = [row[0] for row in all_students_enrolled_query]

            # Find students who have not submitted
            not_submitted_students = [student for student in all_students if student not in students_who_submitted]

            return templates.TemplateResponse("Teacher/view_report.html", {
                "request": request,
                "subject_id": subject_id,
                "class_id": class_id,
                "subject_name": subject,
                "teacher_id": teacher_id,
                "submitted_Students": submitted_students_query,
                "not_submitted_students": not_submitted_students
            })
        else:
            return templates.TemplateResponse("Teacher/view_report.html", {
                "request": request,
                "subject_id": subject_id,
                "class_id": class_id,
                "subject_name": subject,
                "teacher_id": teacher_id,
                "submitted_Students": [],
                "not_submitted_students": []
            })

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)


    
@router.post("/sumbitAssignment", response_class=HTMLResponse)
async def Assignmentt(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject: str = Form(...),
                      studentassignment_file: UploadFile = Form(None),
                      teacher_id: str = Form(None),
                      remarks: str = Form(None),
                      student_id: str = Form(None), db: Session = Depends(get_db), is_auth= Depends(auth_required),
                      is_allowed= Depends(studentAllowed)):

    try:
        # Query the latest assignment
        assignment = db.query(Assignment).filter(Assignment.class_id == class_id, Assignment.subject_id == subject_id).order_by(Assignment.created_at.desc()).first()
        sumbitmsg = None
        if assignment:
            assignment_id = assignment.assignment_id
            teacher_id_ = assignment.teacher_id
            title = assignment.assignment_title
            description = assignment.assignment_description
            due_date = assignment.due_date
            created_at = format_datetime(assignment.created_at)
            link = assignment.link
          

            # Query teacher's full name
            teacher_name = db.query(User.full_name).join(Teacher).filter(Teacher.teacher_id == teacher_id_).first()

            if studentassignment_file and remarks:
                uploads_base = "static/StudentSubmission"

                # Query student information
                student_info = db.query(Student.student_id, User.full_name).join(User).filter(User.user_id == student_id).first()
                student_id = str(student_info[0])
                student_name = str(student_info[1])

                # Create the full path for the file save location
                save_location = os.path.join(uploads_base, class_id, subject_id, subject, student_id, student_name, studentassignment_file.filename)

                # Check if the directory exists and if it contains any files
                directory = os.path.dirname(save_location)
                if os.path.exists(directory):
                    # If the directory exists, remove all files in the directory
                    for file in os.listdir(directory):
                        file_path = os.path.join(directory, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)

                # Ensure the directory exists
                os.makedirs(directory, exist_ok=True)

                # Save the uploaded file
                with open(save_location, "wb") as file_object:
                    shutil.copyfileobj(studentassignment_file.file, file_object)
                
                save_location = save_location.replace("static/","")
                
                # Insert the submission record
                new_submission = Submission(assignment_id=assignment_id, student_id=student_id, file_path=save_location, remarks=remarks)
                db.add(new_submission)
                db.commit()

                # Remove older submissions for the student if a new one is being uploaded
                db.query(Submission).filter(
                    Submission.student_id == student_id
                ).filter(
                    Submission.assignment_id == assignment_id
                ).filter(
                    Submission.submission_id != new_submission.submission_id
                ).delete()

                db.commit()

                sumbitmsg = "Assignment Submitted Successfully !!!"

            return templates.TemplateResponse("assignment.html", {"request": request,
                                                                "subject_id": subject_id,
                                                                "class_id": class_id,
                                                                "subject_name": subject,
                                                                "teacher_name": teacher_name[0],
                                                                "title": title,
                                                                "description": description,
                                                                "due_date": due_date,
                                                                "created_at": created_at,
                                                                "link": link,
                                                                "user_id": teacher_id,
                                                                "teacher_id": teacher_id_,
                                                                "sumbitmsg":sumbitmsg})
        else:
            return templates.TemplateResponse("assignment.html", {"request": request,
                                                                "subject_id": subject_id,
                                                                "class_id": class_id,
                                                                "subject_name": subject,
                                                                "description": None})

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback in case of an error
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
    