from fastapi import APIRouter, Request, Form, Depends, UploadFile
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import shutil
from models.database import Post, User, Comment, Like, Teacher, TeacherClass  # Assuming the necessary models are imported
from utils.utils import format_datetime,get_initials,random_color, get_filename
from models.database import get_db
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

templates.env.filters['initials'] = get_initials

templates.env.filters["random_color"] = random_color

templates.env.filters['getpostname'] = get_filename

# GET route to display class posts
@router.get("/", response_class=HTMLResponse)
async def classroom(request: Request, subject_id: str, subject: str, class_id: str, search_post: str = None, db: Session = Depends(get_db)):
    try:
        # Query for posts
        posts_query = db.query(Post.post_id, Post.user_id, User.full_name, Post.subject_id, Post.class_id,
                               Post.post_content, Post.post_date, Post.filelink).join(User, Post.user_id == User.user_id).filter(
            Post.subject_id == subject_id, Post.class_id == class_id).order_by(Post.post_date.desc())
        
        if search_post:
            posts_query = posts_query.filter(Post.post_content.ilike(f'%{search_post}%'))  # Dynamic search

        posts = posts_query.all()

        # Query for teacher's name
        teacher_name = db.query(User.full_name).join(Teacher, Teacher.user_id == User.user_id).join(TeacherClass, TeacherClass.teacher_id == Teacher.teacher_id).filter(
            TeacherClass.class_id == class_id, TeacherClass.subject_id == subject_id).first()

        formatted_date = format_datetime(posts[0][6]) if posts else ""  # Format date if posts exist

        # Query for comments related to the posts
        comments = db.query(Comment.comment_id, Comment.content, Comment.user_id, Comment.post_id,
                            Post.post_content, Post.post_date, User.full_name.label('commentor_full_name')).join(
            Post, Comment.post_id == Post.post_id).join(User, Comment.user_id == User.user_id).filter(
            Post.class_id == class_id, Post.subject_id == subject_id).all()

        # Query for likes related to the posts
        likes = db.query(Post.post_id, Like.user_id, Like.like_id).join(Like, Post.post_id == Like.post_id).filter(
            Post.class_id == class_id, Post.subject_id == subject_id).all()

        # Retrieve current user and role from session
        current_user = request.session.get("user_id")
        current_role = request.session.get("role")

        # Return the template with the necessary data
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




# POST route to handle form submissions for new posts
@router.post("/", response_class=HTMLResponse)
async def classroom(request: Request, subject_id: str = Form(...), subject: str = Form(...), class_id: str = Form(...),
                     post_content: str = Form(None), file_upload_post: UploadFile = Form(None), db: Session = Depends(get_db)):
    try:
        current_user = request.session.get("user_id")

        if post_content:
            # Save the uploaded file if it exists
            if file_upload_post and file_upload_post.filename:
                uploads_base = "static/PostContents"
                loc = str(class_id) + str(subject_id)
                save_location = os.path.join(uploads_base, str(current_user), loc, file_upload_post.filename)

                # Ensure the directory exists
                directory = os.path.dirname(save_location)
                os.makedirs(directory, exist_ok=True)

                # Save the uploaded file
                with open(save_location, "wb") as file_object:
                    shutil.copyfileobj(file_upload_post.file, file_object)
            else:
                save_location = "nofile"  # If no file is uploaded
            
            # Insert the new post into the database
            new_post = Post(user_id=current_user, subject_id=subject_id, class_id=class_id,
                            post_content=post_content, filelink=save_location.replace('static/', ''))

            db.add(new_post)
            db.commit()

        # Redirect back to the class page with query parameters
        redirect_url = f"/class?subject_id={subject_id}&subject={subject}&class_id={class_id}"
        return RedirectResponse(url=redirect_url, status_code=303)  # Using 303 for redirect after POST

    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
