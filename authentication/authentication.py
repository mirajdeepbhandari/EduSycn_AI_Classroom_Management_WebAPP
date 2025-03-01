from fastapi import HTTPException, Request

async def auth_required(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        request.session["error"] = "You need to sign in before proceeding."
        raise HTTPException(status_code=303, detail="Redirecting", headers={"Location": "/"})
    return True
