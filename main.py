from fastapi import FastAPI, Request, Form, Depends,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import mysql.connector
from mysql.connector import Error
from starlette.middleware.sessions import SessionMiddleware
import random

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
            cursor.execute('SELECT user_id, role FROM user WHERE email=%s AND password=%s', (email, password))
            user = cursor.fetchone()

            if user:
                user_id, role = user
                # Store user_id in the session
                request.session['user_id'] = user_id

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
@app.get("/class", response_class=HTMLResponse)
async def classroom(request: Request, subject_id:str, subject:str, class_id:str):
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
            print(likes)
            
            return templates.TemplateResponse("class.html", {"request": request, "posts":posts, "subject_name":subject,
                                                             "post_time":formatted_date, "comments":comments,"likes":likes
                                                            })
        finally:
            connection.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        return RedirectResponse(url="/", status_code=303)



@app.get("/teacher_dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    return templates.TemplateResponse("Teacher/teacher_landingpage.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
