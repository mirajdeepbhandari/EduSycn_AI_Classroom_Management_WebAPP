import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from authentication.authentication import auth_required
from authentication.authorizations import adminAllowed
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def seekFeedback(request: Request,
                       is_auth= Depends(auth_required)
                       ,is_allowed= Depends(adminAllowed)):
    

    
    
    return templates.TemplateResponse("SUPERADMIN/SeeFeedback.html", {"request": request})