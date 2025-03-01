from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import studentAllowed
from models.database import Notification, Student
from models.database import get_db
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/notifications", response_class=HTMLResponse)
async def notificationsPage(request: Request, db: Session = Depends(get_db),is_auth= Depends(auth_required)
                            , is_allowed= Depends(studentAllowed)):
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