from fastapi import FastAPI, Request, Form, Depends,HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import random
from random import randint
from datetime import datetime, timedelta
import aiosmtplib
from email.message import EmailMessage
import shutil
import os
from database import get_db, User, Student, Classroom, Subject, ClassSubject, Post, User, Comment, Like, Teacher, TeacherClass, Assignment, Submission
from sqlalchemy.orm import Session
from sqlalchemy import func


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="ses")


templates = Jinja2Templates(directory="templates")


# In-memory OTP storage for demo purposes
otp_store = {}

# Email configuration
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587  
EMAIL_USER = "edusync521@gmail.com"  
EMAIL_PASSWORD = "zazi wgrw ofir bmbd" 

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(randint(100000, 999999))

@app.get("/send-otp/")
async def send_otp(email: str = Form(None)):
    """Send OTP to the provided email address."""
    otp = generate_otp()
    email="arbitbhandari17@gmail.com"
    expiry_time = datetime.utcnow() + timedelta(minutes=5) 
    otp_store[email] = {"otp": otp, "expires_at": expiry_time}

    # Create the email message
    try:
        message = EmailMessage()
        message.set_content(f"Your OTP is: {otp}. It is valid for 5 minutes.")
        message["Subject"] = "Your OTP"
        message["From"] = EMAIL_USER
        message["To"] = email

        # Connect to the SMTP server with STARTTLS on port 587
        smtp_client = aiosmtplib.SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT)
        await smtp_client.connect()

        # Login to the SMTP server
        await smtp_client.login(EMAIL_USER, EMAIL_PASSWORD)

        # Send the email
        await smtp_client.send_message(message)

        # Close the connection
        await smtp_client.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"message": "OTP sent successfully"}




@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/register_validation")
async def register_validation(
    full_name: str = Form(...),
    number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    conf_password: str = Form(...),
    db: Session = Depends(get_db),  # Dependency for database session
):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        return RedirectResponse(url="/", status_code=303)
    
    # Check if passwords match
    if password != conf_password:
        return RedirectResponse(url="/", status_code=303)

    # Create a new User instance and add to the database
    new_user = User(
        full_name=full_name,
        number=number,
        email=email,
        password=password,  # You might want to hash the password before storing
        role="student",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/", status_code=303)


@app.post("/login_validation")
async def login_validation(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if the email and password match using SQLAlchemy
    user = db.query(User).filter(User.email == email, User.password == password).first()

    if user:
        # If the user exists, store user details in the session
        request.session['user_id'] = user.user_id
        request.session['user_name'] = user.full_name
        request.session['role'] = user.role

        # Redirect based on the role
        if user.role == "student":
            return RedirectResponse(url="/student_dashboard", status_code=303)
        elif user.role == "teacher":
            return RedirectResponse(url="/teacher_dashboard", status_code=303)
    else:
        # If login fails, redirect back to the login page
        return RedirectResponse(url="/", status_code=303)
    

@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)




@app.get("/student_dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('user_id')
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

        if student_data:
            class_id = student_data[0][2]
            class_name = student_data[0][3]
            # Group subjects and subject_ids
            subjects = [subject[4] for subject in student_data]
            subject_ids = [subject[5] for subject in student_data]
            subject_data = list(zip(subjects, subject_ids))

            return templates.TemplateResponse("student_page.html", {
                "request": request,
                "subject_data": subject_data,
                "class_name": class_name,
                "class_id": class_id
            })

        else:
            # If no data is found for the student, redirect
            return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)
    

def format_datetime(dt):
    # Directly format the datetime object
    formatted_date = dt.strftime('%Y-%m-%d, %I:%M %p')
    return formatted_date

# views.py or utils.py
def get_initials(name):
    parts = str(name).split()
    if len(parts) >= 2:
        initials = parts[0][0] + parts[1][0]
    elif len(parts) == 1:
        initials = parts[0][0]
    else:
        initials = ""
    return initials.upper()

# Register the filter with the Jinja environment
templates.env.filters['initials'] = get_initials


def random_color(value):
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

templates.env.filters["random_color"] = random_color





def get_filename(file_path):
    return file_path.split("\\")[-1]

# Register the filter with the Jinja environment
templates.env.filters['getpostname'] = get_filename



@app.get("/class", response_class=HTMLResponse)
async def classroom(request: Request, subject_id: str, subject: str, class_id: str, db: Session = Depends(get_db)):
    try:
        # Query for posts
        posts = (
            db.query(Post.post_id, Post.user_id, User.full_name, Post.subject_id, Post.class_id,
                    Post.post_content, Post.post_date, Post.filelink)
            .join(User, Post.user_id == User.user_id)
            .filter(Post.subject_id == subject_id, Post.class_id == class_id)
            .order_by(Post.post_date.desc())  
            .all()
        )

        formatted_date = format_datetime(posts[0][6]) if posts else ""

        # Query for comments
        comments = (
            db.query(Comment.comment_id, Comment.content, Comment.user_id, Comment.post_id,
                     Post.post_content, Post.post_date, User.full_name.label('commentor_full_name'))
            .join(Post, Comment.post_id == Post.post_id)
            .join(User, Comment.user_id == User.user_id)
            .filter(Post.class_id == class_id, Post.subject_id == subject_id)
            .all()
        )

        # Query for likes
        likes = (
            db.query(Post.post_id, Like.user_id, Like.like_id)
            .join(Like, Post.post_id == Like.post_id)
            .filter(Post.class_id == class_id, Post.subject_id == subject_id)
            .all()
        )

        # Get current user and role from session
        current_user = request.session.get("user_id")
        current_role = request.session.get("role")

        return templates.TemplateResponse("class.html", {
            "request": request,
            "posts": posts,
            "subject_name": subject,
            "post_time": formatted_date,
            "comments": comments,
            "likes": likes,
            "current_user": current_user,
            "class_id": class_id,
            "subject_id": subject_id,
            "current_role": current_role
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)
    


@app.post("/class", response_class=HTMLResponse)
async def classroom(request: Request, subject_id: str = Form(...), subject: str = Form(...), class_id: str = Form(...),
                     post_content: str = Form(None), file_upload_post: UploadFile = Form(None), db: Session = Depends(get_db)):
    try:
        current_user = request.session.get("user_id")
        
        if post_content:
            # Save the uploaded file if it exists
            if file_upload_post and file_upload_post.filename:
                uploads_base = "static/PostContents"
                loc = str(class_id) + str(subject_id)

                # Create the full path for the file save location
                save_location = os.path.join(uploads_base, str(current_user), loc, file_upload_post.filename)

                # Ensure the directory exists
                directory = os.path.dirname(save_location)
                os.makedirs(directory, exist_ok=True)

                # Save the uploaded file
                with open(save_location, "wb") as file_object:
                    shutil.copyfileobj(file_upload_post.file, file_object)
            else:
                save_location = "nofile"

            # Insert the new post into the database using SQLAlchemy
            new_post = Post(user_id=current_user, subject_id=subject_id, class_id=class_id,
                            post_content=post_content, filelink=save_location)

            db.add(new_post)
            db.commit()

        # Redirect with proper query parameters
        redirect_url = f"/class?subject_id={subject_id}&subject={subject}&class_id={class_id}"
        return RedirectResponse(url=redirect_url, status_code=303)  # Using 303 for redirect after POST

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)





@app.post("/updatePost")
async def feedPostUpdate(
                         request: Request,
                         post_id: str = Form(...),
                          content: str = Form(...),
                          subject_id: str = Form(...),
                          subject: str = Form(...),
                          class_id: str = Form(...),
                          db: Session = Depends(get_db)):
    """
    Update a post's content if the user is authorized.
    """
    try:
  
        # Fetch the post by post_id
        post = db.query(Post).filter(Post.post_id == post_id).first()

        # Update the post content
        post.post_content = content
        db.commit()  # Commit the changes to the database

        # Redirect with the success message
        response = RedirectResponse(url=f"/class?subject_id={subject_id}&subject={subject}&class_id={class_id}", status_code=303)
        response.set_cookie("message", "Post updated successfully", max_age=5)
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback in case of an error
        raise HTTPException(status_code=500, detail="An error occurred while updating the post")



@app.post("/deletePost")
async def deletePost(
    post_id: str = Form(...),
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Delete a post if the user is authorized.
    """
    try:
        # Fetch the file link from the database
        post = db.query(Post).filter(Post.post_id == post_id).first()

        if post:
            filelink = post.filelink

            # Handle file deletion if it exists
            if filelink and filelink != "nofile":
                # Get the directory path of the file
                directory = os.path.dirname(filelink)

                # Check if the file exists and is in a valid directory
                if os.path.exists(filelink) and os.path.isdir(directory):
                    # List all files in the directory
                    files_in_directory = os.listdir(directory)

                    # Check if the directory contains only this file
                    if len(files_in_directory) == 1 and files_in_directory[0] == os.path.basename(filelink):
                        # Remove the file
                        os.remove(filelink)

                        # Remove the directory up to 'static/PostContents'
                        while directory != "static/PostContents" and os.path.exists(directory):
                            if not os.listdir(directory):  # Check if the directory is empty
                                os.rmdir(directory)  # Remove the empty directory
                            directory = os.path.dirname(directory)  # Move to the parent directory
                    else:
                        # Remove only the file if there are other files in the directory
                        os.remove(filelink)

            # Delete the post from the database
            db.delete(post)
            db.commit()

        # Redirect with a success message
        redirect_url = f"/class?subject_id={subject_id}&subject={subject}&class_id={class_id}"
        response = RedirectResponse(url=redirect_url, status_code=303)
        response.set_cookie("message", "Post deleted successfully", max_age=5)
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback the transaction in case of an error
        return RedirectResponse(url="/", status_code=303)

    finally:
        db.close()  # Ensure the database session is properly closed





@app.post("/api/like")
async def like_post(request: Request, db: Session = Depends(get_db)):
    """
    Handle post likes and unlikes. Toggle the like status for a post by a user.
    """
    try:
        # Parse the JSON request body
        data = await request.json()
        post_id = data.get("post_id")
        user_id = data.get("user_id")

        # Validate required fields
        if not post_id or not user_id:
            raise HTTPException(status_code=400, detail="post_id and user_id are required")

        # Check if the user has already liked the post
        like_entry = db.query(Like).filter(Like.post_id == post_id, Like.user_id == user_id).first()

        # Track the action type (like/unlike)
        action = "liked"

        if like_entry:
            # If already liked, delete the like (unlike)
            db.delete(like_entry)
            db.commit()
            action = "unliked"
        else:
            # Otherwise, add a new like
            new_like = Like(post_id=post_id, user_id=user_id)
            db.add(new_like)
            db.commit()

        # Get the updated like count for the post
        like_count = db.query(Like).filter(Like.post_id == post_id).count()

        # Return the updated like count and action type
        return {"likes": like_count, "action": action}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")
    



@app.post("/addComment")
async def addComment(
    request: Request, 
    post_id: str = Form(...),
    comment: str = Form(...), 
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Retrieve the current user ID from the session
        current_user = request.session.get("user_id")
        
        # Insert the comment into the database using SQLAlchemy
        new_comment = Comment(
            post_id=int(post_id),
            user_id=int(current_user),
            content=comment
        )
        db.add(new_comment)
        db.commit()
        
        # Redirect back to the class page
        response = RedirectResponse(
            url=f"/class?subject_id={subject_id}&subject={subject}&class_id={class_id}", 
            status_code=303
        )
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)




@app.get("/api/liked_statuses")
async def get_liked_statuses(user_id: int, db: Session = Depends(get_db)):
    try:
        # Query the likes table for the posts liked by the user
        liked_posts = db.query(Like.post_id).filter(Like.user_id == user_id).all()
        # Extract post IDs from the result
        liked_post_ids = [post_id[0] for post_id in liked_posts]
        return liked_post_ids
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


    
    

@app.post("/classroom_students", response_class=HTMLResponse)
async def showClassMembers(request: Request, subject_id: str = Form(...), subject: str = Form(...), class_id: str = Form(...), db: Session = Depends(get_db)):

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
        
        return templates.TemplateResponse("list_of_students.html", {
            "request": request,
            "listofstu": students,
            "subject_name": subject,
            "class_id": class_id,
            "subject_id": subject_id,
            "subject": subject,
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)




@app.get("/teacher_dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
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

        # Render the teacher dashboard template
        return templates.TemplateResponse(
            "Teacher/teacher_landingpage.html",
            {
                "request": request,
                "teaching_modules": teaching_modules,
                "current_teacher": current_teacher,
            },
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)





@app.post("/give_assignment", response_class=HTMLResponse)
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
    db: Session = Depends(get_db)
 
    
):
    if title and description and due_date:
        connection = establish_connection()

        if connection and connection.is_connected():

           save_location = None

        if assignment_file:
            uploads_base = "static/TeacherAssignment"
            
            # Create the full path for the file save location
            save_location = os.path.join(uploads_base, class_id, subject_id, subject, assignment_file.filename)
            
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
                shutil.copyfileobj(assignment_file.file, file_object)
                
            try:
                # Fetch teacher_id using SQLAlchemy
                teacher = db.query(Teacher).filter(Teacher.user_id == teacher_id).first()
                
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

                # Update the assignment link
                new_assignment.link = save_location
                db.commit()

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
                {"request": request,
                "subject_id": subject_id,
                    "class_id": class_id,
                    "subject_name": subject,
                "message": "Assignment created successfully",
                "teacher_id": teacher_id}
        )

            finally:
                connection.close()
        else:
            return RedirectResponse(url="/", status_code=303)
        
    else:
        # Render the assignment form
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






@app.post("/assignmentview", response_class=HTMLResponse)
async def viewAssignment(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject:str = Form(...), teacher_id: str = Form(...)):
    return templates.TemplateResponse("Teacher/inside_assignment.html", {"request": request,
                                                            "subject_id": subject_id,
                                                            "class_id": class_id,
                                                            "subject_name": subject,
                                                            "teacher_id": teacher_id})



@app.post("/studentReportView", response_class=HTMLResponse)
async def studentMarkReport(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject: str = Form(...), teacher_id: str = Form(...), db: Session = Depends(get_db)):

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
        return RedirectResponse(url="/", status_code=303)


    
@app.post("/sumbitAssignment", response_class=HTMLResponse)
async def Assignmentt(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject: str = Form(...),
                      studentassignment_file: UploadFile = Form(None),
                      teacher_id: str = Form(None),
                      remarks: str = Form(None),
                      student_id: str = Form(None), db: Session = Depends(get_db)):

    # Query the latest assignment
    assignment = db.query(Assignment).filter(Assignment.class_id == class_id, Assignment.subject_id == subject_id).order_by(Assignment.created_at.desc()).first()

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
                                                              "teacher_id": teacher_id_})
    else:
        return templates.TemplateResponse("assignment.html", {"request": request,
                                                              "subject_id": subject_id,
                                                              "class_id": class_id,
                                                              "subject_name": subject,
                                                              "description": None})
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
