from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import re
from models.database import get_db, User

router = APIRouter()

@router.post("/register_validation")
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
        
        existing_user = db.query(User).filter(User.number == number).first()
        if existing_user:
            request.session["error"] = "phone number already exists."
            return RedirectResponse(url="/", status_code=303)
        
        # Hash the password
        hashed_password = bcrypt.hash(password)
        
        # Create a new User instance and add to the database
        new_user = User(
            full_name=full_name,
            number=number,
            email=email,
            password=hashed_password,  # Store the hashed password
            role=None,
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



@router.post("/login_validation")
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
            elif user.role == "admin":
                return RedirectResponse(url="/sa/superadmin", status_code=303)
            else:
                 request.session["error"] = "Please Contact the Admin! for ID Setup"
                 return RedirectResponse(url="/", status_code=303)
        else:
            # If login fails, redirect back to the login page with an error
            request.session["error"] = "Invalid email or password."
            return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        print(f"An error occurred: {e}")
        # Handle database connection or query errors
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)



@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
