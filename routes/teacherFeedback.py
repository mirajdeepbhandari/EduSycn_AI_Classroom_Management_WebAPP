from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session


router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/")
async def feedback_teacher(request: Request):

    return templates.TemplateResponse("feedback.html", {"request": request})



