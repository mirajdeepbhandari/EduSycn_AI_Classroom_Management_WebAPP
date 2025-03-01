from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import  RedirectResponse
from sqlalchemy.orm import Session
from authentication.authentication import auth_required
from models.database import Post, Like, Comment, get_db
import os



router = APIRouter()


@router.post("/updatePost")
async def feedPostUpdate(
                         request: Request,
                         post_id: str = Form(...),
                          content: str = Form(...),
                          subject_id: str = Form(...),
                          subject: str = Form(...),
                          class_id: str = Form(...),
                          db: Session = Depends(get_db),
                          is_auth= Depends(auth_required)):
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




@router.post("/deletePost")
async def deletePost(
    request: Request,
    post_id: str = Form(...),
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required)
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




@router.post("/api/like")
async def like_post(request: Request, db: Session = Depends(get_db),is_auth= Depends(auth_required)):
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
    



@router.post("/addComment")
async def addComment(
    request: Request, 
    post_id: str = Form(...),
    comment: str = Form(...), 
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required)
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




@router.get("/api/liked_statuses")
async def get_liked_statuses(user_id: int, db: Session = Depends(get_db), is_auth= Depends(auth_required)):
    try:
        # Query the likes table for the posts liked by the user
        liked_posts = db.query(Like.post_id).filter(Like.user_id == user_id).all()
        # Extract post IDs from the result
        liked_post_ids = [post_id[0] for post_id in liked_posts]
        return liked_post_ids
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
