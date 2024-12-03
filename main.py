from fastapi import FastAPI, Request, Form, Depends,HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import mysql.connector
from mysql.connector import Error
from starlette.middleware.sessions import SessionMiddleware
import random
from random import randint
from datetime import datetime, timedelta
import aiosmtplib
from email.message import EmailMessage
import shutil
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="ses")


templates = Jinja2Templates(directory="templates")


def establish_connection():
    try:
        # Establish the connection
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='edusync'
        )
        return connection

    except Error as e:
        print(f'Error: {e}')
        return None



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
    request: Request,
    full_name: str = Form(...),
    number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    conf_password: str = Form(...),
):
    connection = establish_connection()

    if connection and connection.is_connected():
        try:
            cursor = connection.cursor()
            # Check if the email already exists
            cursor.execute('SELECT * FROM user WHERE email=%s', (email,))
            record = cursor.fetchone()

            if record:
                return RedirectResponse(url="/", status_code=303)
            elif password != conf_password:
                return RedirectResponse(url="/", status_code=303)
            else:
                # Insert the new user into the database
                cursor.execute(
                    'INSERT INTO user (full_name, number, email, password, role) VALUES (%s, %s, %s, %s, %s)',
                    (full_name, number, email, password, "student"),
                )
                connection.commit()
                return RedirectResponse(url="/", status_code=303)
        finally:
            connection.close()
    else:
        return RedirectResponse(url="/", status_code=303)


@app.post("/login_validation")
async def login_validation(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    connection = establish_connection()

    if connection and connection.is_connected():
        try:
            cursor = connection.cursor()
            # Check if the email and password match
            cursor.execute('SELECT user_id,full_name, role FROM user WHERE email=%s AND password=%s', (email, password))
            user = cursor.fetchone()

            if user:
                user_id,name, role = user
                # Store user_id in the session
                request.session['user_id'] = user_id
                request.session['user_name'] = name
                request.session['role'] = role
                print("user_id:",request.session['user_id'])
                print("role:",request.session['role'])

                # Redirect based on role
                if role == "student":
                    return RedirectResponse(url="/student_dashboard", status_code=303)
                elif role == "teacher":
                    return RedirectResponse(url="/teacher_dashboard", status_code=303)
            else:
                # If login fails, redirect back to the login page
                return RedirectResponse(url="/", status_code=303)
        finally:
            connection.close()
    else:
        return RedirectResponse(url="/", status_code=303)

@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/student_dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    try:
        connection = establish_connection()
        try:
            cursor = connection.cursor()
            query = '''
                    SELECT 
                        student.student_id,
                        student.user_id,
                        student.class_id,
                        classroom.class_name,
                        GROUP_CONCAT(subject.subject_name) AS subject_list,
                        GROUP_CONCAT(subject.subject_id) AS subject_id
                    FROM 
                        student
                    JOIN 
                        classroom ON student.class_id = classroom.class_id
                    JOIN 
                        class_sub ON student.class_id = class_sub.class_id
                    JOIN 
                        subject ON class_sub.subject_id = subject.subject_id
                    WHERE 
                        student.user_id = %s
                    GROUP BY 
                        student.student_id, 
                        student.user_id, 
                        student.class_id, 
                        classroom.class_name
                    ORDER BY 
                        student.student_id;
                                            '''
            cursor.execute(query, (user_id,))
            pass_examinees = cursor.fetchall()
            class_id=pass_examinees [0][2]
            class_name=pass_examinees [0][3]
            subjects=pass_examinees [0][4].split(',')
            sub_id=pass_examinees [0][5].split(',')
            subject_data = list(zip(subjects, sub_id))
            return templates.TemplateResponse("student_page.html", {"request": request, "subject_data":subject_data, "class_name":class_name,
                                                                    "class_id":class_id})
              
        finally:
            connection.close()
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
@app.post("/class", response_class=HTMLResponse)
async def classroom(request: Request, subject_id:str = Form(...), subject:str = Form(...), class_id:str  = Form(...)):
    try:
        connection = establish_connection()
        try:
            cursor = connection.cursor()
            query = '''
                SELECT post.post_id, 
                post.user_id, 
                user.full_name, 
                post.subject_id, 
                post.class_id, 
                post.post_content, 
                post.post_date
            FROM post
            INNER JOIN user ON post.user_id = user.user_id
            WHERE post.subject_id = %s 
            AND post.class_id = %s;
            '''
            comment_query = """
                            SELECT 
                            comments.comment_id, 
                            comments.content, 
                            comments.user_id, 
                            comments.post_id, 
                            post.post_content, 
                            post.post_date,
                            user.full_name AS commentor_full_name
                            
                        FROM 
                            comments
                        JOIN 
                            post ON comments.post_id = post.post_id
                        JOIN 
                            user ON comments.user_id = user.user_id
                        WHERE 
                            post.class_id = %s 
                            AND post.subject_id = %s;

                            """
            like_query = """
                          
                    SELECT  
                    post.post_id,
                    likes.user_id,
                    likes.like_id
                FROM 
                    post
                INNER JOIN 
                    likes ON post.post_id = likes.post_id
                WHERE 
                    post.class_id = %s
                    AND post.subject_id = %s;

                            """
                                      
            cursor.execute(query, (subject_id,class_id))
            posts = cursor.fetchall()
        
            if posts:
                formatted_date=format_datetime(posts[0][6])
            else:
                formatted_date=""

            cursor.execute(comment_query, (class_id,subject_id))
            comments = cursor.fetchall()

            cursor.execute(like_query, (class_id,subject_id))
            likes = cursor.fetchall()
       
            
            current_user=request.session.get("user_id")
            current_role=request.session.get("role")

            
            return templates.TemplateResponse("class.html", {"request": request, "posts":posts, "subject_name":subject,
                                                             "post_time":formatted_date, "comments":comments,"likes":likes,
                                                            "current_user":current_user, "class_id":class_id, "subject_id":subject_id,
                                                            "current_role":current_role})
        finally:
            connection.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)

@app.post("/api/like")
async def like_post(request: Request):
    try:
        # Parse the JSON request body
        data = await request.json()
        post_id_ = data.get("post_id")
        user_id_ = data.get("user_id")

        # Check if post_id and user_id are provided
        if post_id_ is None or user_id_ is None:
            raise HTTPException(status_code=400, detail="post_id and user_id are required")
        
        # Establish connection
        connection = establish_connection()
        
        try:
            cursor = connection.cursor()

            # Check if the user has already liked the post
            cursor.execute("SELECT like_id FROM likes WHERE post_id = %s AND user_id = %s", (post_id_, user_id_))
            result = cursor.fetchone()

            # Initialize a variable to track the action type
            action = "liked"

            if result:
                # If already liked, delete the like (unlike)
                cursor.execute("DELETE FROM likes WHERE post_id = %s AND user_id = %s;", (post_id_, user_id_))
                connection.commit()
                action = "unliked"
            else:
                # Otherwise, insert a new like
                cursor.execute("INSERT INTO likes (post_id, user_id) VALUES (%s, %s);", (post_id_, user_id_))
                connection.commit()

            # Get the updated like count
            cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id_,))
            like_count = cursor.fetchone()[0]

            # Return the updated like count and action type
            return {"likes": like_count, "action": action}
        
        finally:
            # Ensure the connection is always closed
            connection.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

@app.get("/api/liked_statuses")
async def get_liked_statuses(user_id: int):
    connection = establish_connection()
    try:
        cursor = connection.cursor()
        # Get the post_ids that the user has liked
        cursor.execute("SELECT post_id FROM likes WHERE user_id = %s", (user_id,))
        liked_posts = [row[0] for row in cursor.fetchall()]
        return liked_posts
    finally:
        connection.close()

@app.post("/classroom_students", response_class=HTMLResponse)
async def showClassMembers(request: Request, subject_id:str = Form(...), subject:str = Form(...), class_id:str = Form(...)):

    try:
        connection = establish_connection()
        try:
            cursor = connection.cursor()

            query_students = '''
               SELECT u.full_name
                FROM user u
                JOIN student s ON u.user_id = s.user_id
                JOIN class_sub cs ON s.class_id = cs.class_id
                WHERE u.role = 'student'
                AND s.class_id = %s
                AND cs.subject_id = %s;
            '''
           
                                      
            cursor.execute(query_students, (class_id,subject_id))
            students = cursor.fetchall()
            print(students)
            return templates.TemplateResponse("list_of_students.html", {"request": request, 
                                                                        "listofstu":students,
                                                                        "subject_name":subject,
                                                                        "class_id":class_id,
                                                                        "subject_id":subject_id,
                                                                         "subject":subject})
        
        finally:
            connection.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)

@app.get("/teacher_dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    current_teacher = request.session.get('user_name')
    current_user_id = request.session.get('user_id')

    try:
        connection = establish_connection()
        try:
            cursor = connection.cursor()

            query = '''
               SELECT 
                    t.user_id,
                    t.teacher_id,
                    tc.class_id,
                    c.class_name,
                    tc.subject_id,
                    s.subject_name
                FROM 
                    teacher_class AS tc
                INNER JOIN teacher AS t ON tc.teacher_id = t.teacher_id
                INNER JOIN classroom AS c ON c.class_id = tc.class_id
                INNER JOIN subject AS s ON s.subject_id = tc.subject_id
                WHERE t.user_id = %s
                ORDER BY tc.class_id ASC;

            '''
           
            cursor.execute(query, (current_user_id,))
            teaching_modules = cursor.fetchall()
            return templates.TemplateResponse("Teacher/teacher_landingpage.html", {"request": request, 
                                                                                   "teaching_modules": teaching_modules, 
                                                                                   "current_teacher": current_teacher})
        
        finally:
            connection.close()

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
    assignment_file: UploadFile = Form(None)
 
    
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
                cursor = connection.cursor()
            

                cursor.execute("SELECT teacher_id FROM teacher WHERE user_id = %s", (teacher_id,))
                teacher = cursor.fetchone()
                       
                sql_query = """
                        INSERT INTO assignment 
                        (teacher_id, class_id, subject_id, assignment_title, assignment_description, due_date) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                data = (teacher[0], class_id, subject_id, title, description, due_date)

                cursor.execute(sql_query, data)

                connection.commit()

                cursor.execute("UPDATE assignment SET link = %s where class_id = %s AND subject_id = %s", (save_location,class_id,subject_id,))

                connection.commit()

                cursor.execute(
                                """
                                DELETE FROM assignment 
                                WHERE class_id = %s 
                                AND subject_id = %s 
                                AND created_at < (
                                    SELECT MAX(created_at) 
                                    FROM assignment 
                                    WHERE class_id = %s 
                                    AND subject_id = %s
                                );
                                """, 
                                (class_id, subject_id, class_id, subject_id)
                            )

                connection.commit()

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
async def studentMarkReport(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject:str = Form(...), teacher_id: str = Form(...)):

        try:
            connection = establish_connection()
            try:
                cursor = connection.cursor()

                query = """
                            SELECT 
                                u.full_name AS student_name,
                                s.submission_date AS submission_time,
                                s.file_path AS submission_link,
                                a.assignment_title AS assignment_title
                            FROM 
                                submission s
                            JOIN 
                                assignment a ON s.assignment_id = a.assignment_id
                            JOIN 
                                student st ON s.student_id = st.student_id
                            JOIN 
                                user u ON st.user_id = u.user_id
                            WHERE 
                                st.class_id = %s AND a.subject_id = %s;

                        """
                
                cursor.execute(query, (class_id,subject_id))

                submitted_Students = cursor.fetchall()

                if submitted_Students:

                        students_who_submitted = [row[0] for row in submitted_Students]
                        

                        all_students_enrolled = """

                                            SELECT 
                                                DISTINCT u.full_name AS student_name
                                            FROM 
                                                student st
                                            JOIN 
                                                user u ON st.user_id = u.user_id
                                            JOIN 
                                                assignment a ON a.class_id = st.class_id
                                            WHERE 
                                                st.class_id = 10 AND a.subject_id = 1;


                                            """

                        cursor.execute(all_students_enrolled)

                        all_students = cursor.fetchall()
                        
                        all_students = [row[0] for row in all_students]

                        not_submitted_students = [student for student in all_students if student not in students_who_submitted]

                        
                        return templates.TemplateResponse("Teacher/view_report.html", {"request": request,
                                                                    "subject_id": subject_id,
                                                                    "class_id": class_id,
                                                                    "subject_name": subject,
                                                                    "teacher_id": teacher_id,
                                                                    "submitted_Students": submitted_Students,
                                                                    "not_submitted_students": not_submitted_students})

                else:
                    submitted_Students=[]
                    not_submitted_students=[]
                    return templates.TemplateResponse("Teacher/view_report.html", {"request": request,
                                                                    "subject_id": subject_id,
                                                                    "class_id": class_id,
                                                                    "subject_name": subject,
                                                                    "teacher_id": teacher_id,
                                                                    "submitted_Students": submitted_Students,
                                                                    "not_submitted_students": not_submitted_students
                                                                    })

            finally:
                connection.close()

        except Exception as e:
            print(f"An error occurred: {e}")
            return RedirectResponse(url="/", status_code=303)




 

@app.post("/sumbitAssignment", response_class=HTMLResponse)
async def Assignment(request: Request, subject_id: str = Form(...), class_id: str = Form(...), subject:str = Form(...),
                     studentassignment_file: UploadFile = Form(None),
                     teacher_id: str = Form(None),
                     remarks: str = Form(None),
                     student_id: str = Form(None)):

        connection = establish_connection()
        

        if connection and connection.is_connected():
            try:
                cursor = connection.cursor()

                cursor.execute("SELECT * from assignment WHERE class_id = %s AND subject_id = %s ORDER BY created_at DESC LIMIT 1;", (class_id,subject_id))

                Assignment = cursor.fetchone()
                if Assignment:
                    assignment_id=Assignment[0]
                    teacher_id_=Assignment[1]
                    title=Assignment[4]
                    description=Assignment[5]
                    due_date=Assignment[6]
                    created_at=format_datetime(Assignment[7])
                    link=Assignment[8]

                    cursor.execute("SELECT u.full_name FROM teacher AS t JOIN user AS u ON t.user_id = u.user_id WHERE t.teacher_id = %s;", (teacher_id_,))
                    teacher_name = cursor.fetchone()

                    if studentassignment_file and remarks:
                      

                        # Save the uploaded file

                        uploads_base = "static/StudentSubmission"

                        cursor.execute("SELECT S.student_id,u.full_name FROM student AS S JOIN user AS u ON S.user_id = u.user_id WHERE u.user_id = %s;", (student_id,))
                        student_info = cursor.fetchone()
                        student_id=str(student_info[0])
                        student_name=str(student_info[1])
            
                        # Create the full path for the file save location
                        save_location = os.path.join(uploads_base, class_id, subject_id, subject,student_id,student_name, studentassignment_file.filename)
                        
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

                        
                        cursor.execute("INSERT INTO submission (assignment_id, student_id, file_path, remarks) VALUES (%s, %s, %s, %s);",
                        (assignment_id, student_id, save_location, remarks))

                        connection.commit()

                        cursor.execute(
                                """
                                DELETE FROM submission
                                WHERE student_id = %s
                                and assignment_id = %s
                                AND submission_date < (
                                    SELECT MAX(submission_date)
                                    FROM submission
                                    WHERE student_id = %s
                                    AND assignment_id = %s
                                );
                                """,
                                (int(student_id), int(assignment_id), int(student_id), int(assignment_id))
                            )

                        connection.commit()


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
                                                        })
                else:
                     return templates.TemplateResponse("assignment.html", {"request": request,
                                                            "subject_id": subject_id,
                                                            "class_id": class_id,
                                                            "subject_name": subject,
                                                            "description": None,
                                                            })
                

            finally:
                connection.close()
        else:
            return RedirectResponse(url="/", status_code=303)
        

    




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
