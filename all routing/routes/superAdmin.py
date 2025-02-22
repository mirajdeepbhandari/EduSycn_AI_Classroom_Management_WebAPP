import json
from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from models.database import Classroom, Student, Subject, Teacher, TeacherClass, User, get_db
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/superadmin", response_class=HTMLResponse)
async def superadmin_root(request: Request, db: Session = Depends(get_db)):
    try:
        pending_users = db.query(User.user_id, User.full_name, User.email,
                                 User.number).filter(User.role == None).all()
      
        return templates.TemplateResponse("SUPERADMIN/dashboard.html", {"request": request, "PendingUsers": pending_users})
       
    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)


@router.post("/sa_removeUser", response_class=HTMLResponse)
async def delete_user(request: Request, user_id: int = Form(...), db: Session = Depends(get_db)):
    try:
        user= db.query(User).filter(User.user_id == user_id).first()
        db.delete(user)
        db.commit()
        return RedirectResponse(url="/sa/superadmin", status_code=303)
       
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)  
    
    
@router.post("/sa_setUser", response_class=HTMLResponse)
async def set_user(request: Request, user_id: int = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    try:
        user= db.query(User).filter(User.user_id == user_id).first()
        user.role = role
        db.commit()
        if role == "teacher":
            teacher=Teacher(user_id=user_id)
            db.add(teacher)
            db.commit()
        return RedirectResponse(url="/sa/superadmin", status_code=303)
       
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)  



@router.get("/sa_assignUserClass", response_class=HTMLResponse)
async def assignuUserClass(request: Request, db: Session = Depends(get_db)):
    try:
        pending_class_users = db.query(User.user_id, User.full_name, User.email,
                                 User.number).filter(User.role == "student", User.status == "pending").all()
        
        classes = db.query(Classroom.class_id, Classroom.class_name).all()
      
        return templates.TemplateResponse("SUPERADMIN/AssignPage.html", {"request": request, "PendingClassUsers": pending_class_users,"Classes_": classes})
       
    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
    


@router.post("/set_userClass", response_class=HTMLResponse)
async def set_userClass(
    request: Request, 
    user_id: int = Form(...), 
    class_choice: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        new_student = Student(user_id=user_id, class_id=class_choice)
        db.add(new_student)  
        db.commit()
        db.query(User).filter(User.user_id == user_id).update({User.status: "approved"})
        db.commit()
        return RedirectResponse(url="/sa/sa_assignUserClass", status_code=303)
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
    



@router.get("/sa_AssignTeacherListings", response_class=HTMLResponse)
async def AssignTeacherListings(request: Request, db: Session = Depends(get_db)):
    try:
        pending_class_users = db.query(User.user_id, User.full_name, User.email,
                                 User.number).filter(User.role == "teacher", User.status == "pending").all()
        
        return templates.TemplateResponse("SUPERADMIN/AssignTeacherListings.html", {"request": request, "PendingClassTeachers": pending_class_users})
       
    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)




@router.get("/sa_AssignTeacher", response_class=HTMLResponse)
async def AssignTeacher(request: Request, user_id: str  , user_name: str , db: Session = Depends(get_db)):
    try:

        classes = db.query(Classroom.class_id, Classroom.class_name).all()
        subjects = db.query(Subject.subject_id, Subject.subject_name).all()
        error=request.session.get("error", None)
        return templates.TemplateResponse("SUPERADMIN/AssignTeacher.html", {"request": request, "userId": user_id, 
                                                                            "userName": user_name,
                                                                             "Classes_": classes, "Subjects_": subjects,
                                                                             "error": error})
    except Exception as e:
        print(f"An error occurred: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)



@router.post("/assignclass-sub", response_class=HTMLResponse)
async def AssignClassSub(request: Request, datalist: list = Form(...), user_id: str = Form(...), user_name: str = Form(...),
                           db: Session = Depends(get_db)):
    teachers = []
    try:
       data_list = json.loads(datalist[0])
       teacherID = db.query(Teacher.teacher_id).filter(Teacher.user_id == user_id).first()
       teacherID = teacherID[0]
       for data in data_list:
            already_exist = db.query(TeacherClass.tc_id).filter(
                TeacherClass.class_id == data["class"], TeacherClass.subject_id == data["subject"]
            ).first()
            if already_exist:
                request.session["error"] = f"Teacher Already Assigned With This Class {data['class']}  & Subject {data['subject']} !!!"
                return RedirectResponse(url=f"/sa/sa_AssignTeacher?user_id={user_id}&user_name={user_name}", status_code=303)
            
            teacher = TeacherClass(
            teacher_id=teacherID,
            class_id=data['class'],  
            subject_id=data['subject'])
            teachers.append(teacher)
        
       db.bulk_save_objects(teachers)
       db.commit()

       db.query(User).filter(User.user_id == user_id).update({User.status: "approved"})
       db.commit()

       return RedirectResponse(url="/sa/sa_AssignTeacherListings", status_code=303)
       
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)
