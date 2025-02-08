import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Form, Depends,HTTPException, UploadFile, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from random import randint, random
from datetime import datetime, timedelta, timezone
import aiosmtplib
from email.message import EmailMessage
import shutil
import os
from database import (Chatroom, McqMarks, Notification, get_db, User, Student, Classroom, Subject, ClassSubject, Post, User, Comment, Like, Teacher, TeacherClass, Assignment, Submission,
 Message)
from sqlalchemy.orm import Session
from sqlalchemy import func
from utils.utils import format_datetime,get_initials,random_color,get_filename,parse_questions,parse_json
import re
from passlib.hash import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from services.AIServices.McqGenerator import PDFMCQGenerator
import json


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="ses")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains to access the API (adjust as needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


templates = Jinja2Templates(directory="templates")

# Register the filter with the Jinja environment

templates.env.filters['initials'] = get_initials

templates.env.filters["random_color"] = random_color

templates.env.filters['getpostname'] = get_filename


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
    error = request.session.pop("error", None)
    success = request.session.pop("success", None)
    return templates.TemplateResponse("login.html", {"request": request,"error": error, "success": success})



@app.post("/register_validation")
async def register_validation(
    request: Request,
    full_name: str = Form(...),
    number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    conf_password: str = Form(...),
    db: Session = Depends(get_db),
):
   try: 
        # Check if the full name length is greater than 5
        if len(full_name) <= 5:
            request.session["error"] = "Enter a valid full name (more than 5 characters)."
            return RedirectResponse(url="/", status_code=303)

        # Validate full name (no symbols or numbers allowed)
        if not full_name.replace(" ", "").isalpha():
            request.session["error"] = "Full name must contain only letters"
            return RedirectResponse(url="/", status_code=303)
        
        # Validate phone number (10 digits)
        if not re.fullmatch(r"\d{10}", number):
            request.session["error"] = "Phone number must be 10 digits."
            return RedirectResponse(url="/", status_code=303)
        
        # Validate email format
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.fullmatch(email_regex, email):
            request.session["error"] = "Invalid email format."
            return RedirectResponse(url="/", status_code=303)
        
        # Validate password (at least 8 characters, 1 special symbol, 1 number, 1 uppercase letter, 1 lowercase letter)
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.fullmatch(password_regex, password):
            request.session["error"] = (
                "Password must be 8+ characters with uppercase, lowercase, number, and special character."
            )
            return RedirectResponse(url="/", status_code=303)
        
        # Check if passwords match
        if password != conf_password:
            request.session["error"] = "Passwords do not match."
            return RedirectResponse(url="/", status_code=303)
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            request.session["error"] = "Email already exists."
            return RedirectResponse(url="/", status_code=303)
        
        # Hash the password
        hashed_password = bcrypt.hash(password)
        
        # Create a new User instance and add to the database
        new_user = User(
            full_name=full_name,
            number=number,
            email=email,
            password=hashed_password,  # Store the hashed password
            role="student",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        request.session["success"] = "Registration successful!"
        return RedirectResponse(url="/", status_code=303)

   except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback in case of error
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)



@app.post("/login_validation")
async def login_validation(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Fetch the user by email
        user = db.query(User).filter(User.email == email).first()

        if user and bcrypt.verify(password, user.password):
            # If the user exists and password matches, store user details in the session
            request.session['user_id'] = user.user_id
            request.session['user_name'] = user.full_name
            request.session['role'] = user.role

            # Redirect based on the role
            if user.role == "student":
                return RedirectResponse(url="/student_dashboard", status_code=303)
            elif user.role == "teacher":
                return RedirectResponse(url="/teacher_dashboard", status_code=303)
        else:
            # If login fails, redirect back to the login page with an error
            request.session["error"] = "Invalid email or password."
            return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")
        # Handle database connection or query errors
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)



    
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)



@app.get("/student_dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, search_query: str = None, db: Session = Depends(get_db)):
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

    



@app.get("/class", response_class=HTMLResponse)
async def classroom(request: Request, subject_id: str, subject: str, class_id: str, search_post: str = None, db: Session = Depends(get_db)):
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
        
        if search_post:
            posts = (
                db.query(
                    Post.post_id, Post.user_id, User.full_name, Post.subject_id, Post.class_id,
                    Post.post_content, Post.post_date, Post.filelink
                )
                .join(User, Post.user_id == User.user_id)
                .filter(
                    Post.subject_id == subject_id,
                    Post.class_id == class_id,
                    Post.post_content.ilike(f'%{search_post}%')  # Dynamically insert the variable
                )
                .order_by(Post.post_date.desc())
                .all()
            )

        # Query for teachername
        teacher_name = (
            db.query(User.full_name)
            .join(Teacher, Teacher.user_id == User.user_id)
            .join(TeacherClass, TeacherClass.teacher_id == Teacher.teacher_id)
            .filter(TeacherClass.class_id == class_id, TeacherClass.subject_id == subject_id)
            .first()
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
            "current_role": current_role,
            "teacher": teacher_name[0] if teacher_name else "Unassigned",
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
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
        request.session["error"] = "Something Went Wrong on Server !!!"
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
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)




@app.post("/deletePost")
async def deletePost(
    request: Request,
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
        db.rollback()  # Rollback in case of an error
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)




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
        db.rollback()  # Rollback in case of an error
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
    



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
        db.rollback()  # Rollback in case of an error
        request.session["error"] = "Something Went Wrong on Server !!!"
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




@app.get("/teacher_dashboard", response_class=HTMLResponse)
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
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)


    
@app.post("/sumbitAssignment", response_class=HTMLResponse)
async def Assignmentt(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject: str = Form(...),
                      studentassignment_file: UploadFile = Form(None),
                      teacher_id: str = Form(None),
                      remarks: str = Form(None),
                      student_id: str = Form(None), db: Session = Depends(get_db)):

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
    

# notifications

@app.get("/notifications", response_class=HTMLResponse)
async def notificationsPage(request: Request, db: Session = Depends(get_db)):
    current_user = request.session.get("user_id")
    try:
        result = db.query(Student.class_id).filter(Student.user_id == current_user).first()
        # Query for students who have submitted the assignment
        latest_notifications = db.query(Notification.content, Notification.date).filter(Notification.which_class == result[0]).order_by(Notification.date.desc()).limit(10).all()
        db.query(Student).filter(Student.user_id == current_user).update({Student.is_notifyread: 'yes'})
        db.commit()
        return templates.TemplateResponse("notify.html", {"request": request, "notifications": latest_notifications})
       
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback in case of an error
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)



# chat part below

@app.get("/inbox", response_class=HTMLResponse)
async def inbox(
    request: Request,
    searched_user: str = None,
    db: Session = Depends(get_db)
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

   


@app.get("/chatListings", response_class=HTMLResponse)
async def Listings(request: Request,
                   user_id: str,
                   user_name: str,
                   db: Session = Depends(get_db)):
    
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



@app.get("/get_unread_counts", response_class=JSONResponse)
async def get_unread_counts(request: Request, db: Session = Depends(get_db)):
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

        # Create a dictionary with sender_id as the key and total unread messages as the value
        unread_count_dict = {row.sender_id: row.total_unread for row in unread_message_counts}
        
        return unread_count_dict
    except Exception as e:
        return {"error": str(e)}



# summarize page
@app.get("/summary_note", response_class=HTMLResponse)
async def summaryNote(request: Request):
    return templates.TemplateResponse("summarize_page.html", {"request": request})






@app.get("/generatemcq", response_class=HTMLResponse)
async def GenerateMcqPage(
    request: Request,
    subject_id: str,
    subject: str,
    class_id: str,
    mcq_output: str = None,
    db: Session = Depends(get_db)
):
    file_path = "jsonDB/mcq_data.json"
    mcq_output_json = None

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Load or create JSON file
        if not os.path.exists(file_path):
            mcq_data = {}
            with open(file_path, 'w') as json_file:
                json.dump(mcq_data, json_file, indent=4)
        else:
            with open(file_path, 'r') as json_file:
                try:
                    mcq_data = json.load(json_file)
                except json.JSONDecodeError:
                    mcq_data = {}

        # Extract MCQ questions safely
        mcq_json = (
            mcq_data
            .get(f"class_{class_id}", {})
            .get("subjects", {})
            .get(subject_id, {})
            .get("questions", {})
        )

        if mcq_json:
            mcq_output_json = parse_json(mcq_json).strip().replace("*", "")

    except Exception as e:
        print(f"An error occurred while handling JSON: {e}")

    try:
        exam_marks = (
            db.query(McqMarks.student_id, McqMarks.user_name, McqMarks.marks, McqMarks.percentage)
            .filter(McqMarks.class_id == class_id, McqMarks.subject_id == subject_id)
            .all()
        )

    except Exception as e:
        print(f"Database error: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "TEACHER/generate_mcq.html",
        {
            "request": request,
            "subject_id": subject_id,
            "subject": subject,
            "class_id": class_id,
            "textout_mcq": mcq_output,
            "mcq_from_json": mcq_output_json,
            "examMarks": exam_marks
        }
    )

@app.post("/generatemcq", response_class=HTMLResponse)
async def GenerateMcqPage(
    pdf_file: UploadFile = File(...),
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...)
):
    # Create the directory if it doesn't exist
    directory_path = f"static/PDFProcessing/{class_id}/{subject_id}/{subject}"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename (prevent issues with slashes or invalid characters)
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")

    # Define file path correctly
    file_location = os.path.join(directory_path, safe_filename)

    # Save the uploaded file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())

    # Process the PDF and generate MCQs
    api_key = "AIzaSyBGUzqgoBtsxiTg4SH41eXD60IvOWoVD_o"
    mcq_generator = PDFMCQGenerator(file_location, api_key)
    textout = mcq_generator.run()

    # Delete the uploaded PDF file
    directory = os.path.dirname(file_location )
    print(directory)
    if os.path.exists(directory):
        # If the directory exists, remove all files in the directory
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    
    # Redirect to GET route with necessary data
    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}&mcq_output={textout}"
    return RedirectResponse(url=f"/generatemcq{query_params}", status_code=303)


@app.post("/publishmcq", response_class=HTMLResponse)
async def publishMcq(request: Request,
                      subject_id: str = Form(...),
                      subject: str = Form(...),
                      class_id: str = Form(...),
                      mcq_text: str = Form(...)):

    # Assuming parse_questions is a function that returns questions data
    ans = parse_questions(mcq_text)
    
    # Define the file path where you want to save the JSON data
    file_path = 'jsonDB/mcq_data.json'

    # Try to read the existing data from the file
    try:
        with open(file_path, 'r') as json_file:
            mcq_data = json.load(json_file)
    except FileNotFoundError:
        # If file doesn't exist, initialize an empty structure
        mcq_data = {}

    # Ensure the class exists in the data
    if f"class_{class_id}" not in mcq_data:
        mcq_data[f"class_{class_id}"] = {
            "subjects": {}
        }

    # Check if the subject already exists under the class
    if subject_id not in mcq_data[f"class_{class_id}"]["subjects"]:
        mcq_data[f"class_{class_id}"]["subjects"][subject_id] = {
            "questions": ans
        }
    else:
        # If subject exists, append the questions to the existing ones
        mcq_data[f"class_{class_id}"]["subjects"][subject_id]["questions"].update(ans)

    # Save the updated JSON data back to the file
    with open(file_path, 'w') as json_file:
        json.dump(mcq_data, json_file, indent=2)

    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}"
    return RedirectResponse(url=f"/generatemcq{query_params}", status_code=303) 



@app.post("/deletemcq", response_class=HTMLResponse)
async def deleteMcq(request: Request,
                     subject_id: str = Form(...),
                     subject: str = Form(...),
                     class_id: str = Form(...),
                     db: Session = Depends(get_db)):

    try:
        # Open the JSON file
        with open('jsonDB/mcq_data.json', 'r') as json_file:
            mcq_data = json.load(json_file)

        # Check if the specified class and subject exist
        class_key = f"class_{class_id}"
        if class_key in mcq_data and "subjects" in mcq_data[class_key]:
            subjects = mcq_data[class_key]["subjects"]
            if subject_id in subjects:
                # Remove the subject
                subjects.pop(subject_id)
                # Save the updated JSON back to the file
                with open('jsonDB/mcq_data.json', 'w') as json_file:
                    json.dump(mcq_data, json_file, indent=2)
            else:
                message = f"Subject with ID {subject_id} does not exist."
        else:
            message = f"Class {class_id} or subjects not found."

    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
    
    try:
       db.query(McqMarks).filter(McqMarks.class_id == class_id, McqMarks.subject_id == subject_id).delete()
       db.commit()    
    except Exception as e:
        print(e)
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}"
    return RedirectResponse(url=f"/generatemcq{query_params}", status_code=303) 






@app.get("/mcqpage", response_class=HTMLResponse)
async def McqPageStudent(request: Request,
                         subject_id: str,
                         subject: str,
                         class_id: str,
                         db: Session = Depends(get_db)):
    
    try:
        studentID = db.query(Student.student_id).filter(Student.user_id==request.session.get('user_id')).first()
        studentID=studentID[0]
        is_exam_taken = db.query(McqMarks.is_taken).filter(McqMarks.class_id == class_id,McqMarks.subject_id == subject_id,McqMarks.student_id == studentID).first()
        if is_exam_taken:
            is_exam_taken = is_exam_taken[0]
            if is_exam_taken == 'yes':
                return RedirectResponse(url="/exam_submission_status", status_code=303)
    except Exception as e:
        print(e)
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    
    fullmarks=""
    passmarks=""
    ques=None

    student_ = request.session.get('user_name')
    studentid_ = request.session.get('user_id')
    
    try:
        # Open the JSON file
        with open('jsonDB/mcq_data.json', 'r') as json_file:
            mcq_data = json.load(json_file)

        
        mcq_json = mcq_data.get(f"class_{class_id}", {}).get("subjects", {}).get(subject_id, {}).get("questions", {})
       
        if len(mcq_json) == 0:
            ques=None
        
        else:

            fullmarks= len(mcq_json)
            passmarks= int((len(mcq_json)/2)-2)
            ques= mcq_json
      


    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
    

    return templates.TemplateResponse("mcqpage.html", {"request": request,
                                                       "questions":ques,
                                                       "fullmark":fullmarks,
                                                       "passmark":passmarks, 
                                                       "subject_id": subject_id,
                                                       "subject": subject,
                                                        "class_id": class_id,
                                                        "studentname": student_,
                                                        "studentid": studentid_})


@app.post("/submit_mcq")
async def submitMcq(request: Request,
                        subject_id: str = Form(...),
                        subject: str = Form(...),
                        class_id: str = Form(...),
                        student_id: str = Form(...),
                        student_name: str = Form(...),
                        db: Session = Depends(get_db)):
    
    form_data = await request.form() 
    answers = dict(form_data)  # Convert to dictionary

    with open("jsonDB/mcq_data.json", 'r') as json_file:
            mcq_data = json.load(json_file)
            
    # Validate answers
    if (subjects := mcq_data.get(f"class_{class_id}", {}).get("subjects")) and subject_id in subjects:
        correct_count = 0
        total_questions = len(answers)

        for q_num, user_answer in answers.items():
            question_id = q_num.replace("question", "")
            correct_answer = subjects[subject_id]["questions"].get(question_id, {}).get("correct_answer")

            if correct_answer and user_answer == correct_answer:
                correct_count += 1

        accuracy = (correct_count / total_questions) * 100

    try:
       
        studentID = db.query(Student.student_id).filter_by(user_id=student_id).first()
        
        marks = McqMarks(student_id=studentID[0],
                        user_name=student_name,
                        class_id=class_id,
                        subject_id=subject_id,
                        marks=correct_count,
                        percentage=accuracy,
                        is_taken="yes")
        
        db.add(marks)
        db.flush() 
        db.refresh(marks)  
        db.commit()
        
    except Exception as e:
        return {"error": str(e)}

    return templates.TemplateResponse("thankyoupage.html", {"request": request, "subject_name": subject})





@app.get("/exam_submission_status", response_class=HTMLResponse)
async def examSubmissionStatus(request: Request):
    return templates.TemplateResponse("examalreadysubmission.html", {"request": request})









# chat 

class ConnectionManager:
    def __init__(self):
        # Store active connections: {chat_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str, user_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}
        self.active_connections[chat_id][user_id] = websocket

    def disconnect(self, chat_id: str, user_id: str):
        if chat_id in self.active_connections:
            if user_id in self.active_connections[chat_id]:
                del self.active_connections[chat_id][user_id]
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def send_message(self, message: dict, chat_id: str, sender_id: str):
        if chat_id in self.active_connections:
            # Send to all users in the chat except sender
            for user_id, connection in self.active_connections[chat_id].items():
                if user_id != sender_id:
                    await connection.send_json(message)
                    return True  # Indicates message was delivered
        return False  # Indicates message couldn't be delivered

manager = ConnectionManager()




@app.websocket("/ws/{chat_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_id: int,  # Changed to int to match your schema
    user_id: int,  # Changed to int to match your schema
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, str(chat_id), str(user_id))
    try:
        while True:
            data = await websocket.receive_json()
            
            # Get chatroom to determine receiver_id
            chatroom = db.query(Chatroom).filter(Chatroom.chat_id == chat_id).first()
            receiver_id = chatroom.user2_id if user_id == chatroom.user1_id else chatroom.user1_id
            
            # Create new message
            message = Message(
                content=data["message"],
                chat_id=chat_id,
                sender_id=user_id,
                receiver_id=receiver_id,
                timestamp=func.now(),
            )
            db.add(message)
            db.flush()  # Get the message ID without committing
            
            # Prepare message data
            message_data = {
                "msg_id": message.msg_id,
                "content": message.content,
                "sender_id": user_id,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
            
            # Try to deliver the message
            await manager.send_message(message_data, str(chat_id), str(user_id))
            
            db.commit()
            
    except WebSocketDisconnect:
        manager.disconnect(str(chat_id), str(user_id))


@app.get("/api/messages/{chat_id}")
async def get_messages(
    chat_id: int,
    db: Session = Depends(get_db)
):
    try:
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.timestamp)
            .all()
        )
        
        return [
            {
                "msg_id": msg.msg_id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    

class ActiveUsersResponse(BaseModel):
    active_users: List[str]
    total_users: int

@app.get("/active-users", response_model=ActiveUsersResponse)
async def get_active_users():
    """
    Returns a list of all active user IDs across all chats.
    Returns:
        {
            "active_users": ["user1", "user2", "user3"],
            "total_users": 3
        }
    """
    try:
        # Get unique user IDs from all chats
        unique_users = set()
        for chat_users in manager.active_connections.values():
            unique_users.update(chat_users.keys())
            
        return ActiveUsersResponse(
            active_users=list(unique_users),
            total_users=len(unique_users)
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch active users: {str(e)}"
        )


@app.get("/get_unread_counts", response_class=JSONResponse)
async def get_unread_counts(request: Request, db: Session = Depends(get_db)):
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

        # Create a dictionary with sender_id as the key and total unread messages as the value
        unread_count_dict = {str(row.sender_id): row.total_unread for row in unread_message_counts}
        
        return unread_count_dict
    except Exception as e:
        print(f"Error in get_unread_counts: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
