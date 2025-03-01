from fastapi import HTTPException, Request

async def teacherAllowed(request: Request):
    user_role= request.session.get("role")
    if user_role != "teacher":
        raise HTTPException(status_code=303, detail="Redirecting", headers={"Location": "/404"})
    return True

async def studentAllowed(request: Request):
    user_role= request.session.get("role")
    if user_role != "student":
        raise HTTPException(status_code=303, detail="Redirecting", headers={"Location": "/404"})
    return True

async def adminAllowed(request: Request):
    user_role= request.session.get("role")
    if user_role != "admin":
        raise HTTPException(status_code=303, detail="Redirecting", headers={"Location": "/404"})
    return True

async def teacher_student_Allowed(request: Request):
    user_role= request.session.get("role")
    if user_role == "admin":
        raise HTTPException(status_code=303, detail="Redirecting", headers={"Location": "/404"})
    return True


