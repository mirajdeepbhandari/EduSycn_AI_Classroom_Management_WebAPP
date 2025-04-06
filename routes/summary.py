from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import studentAllowed
from models.database import get_db
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
import os
from services.AIServices.Summarize import SummarizePDF

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def summaryNote(request: Request,
                      summary: str = None,
                       is_auth= Depends(auth_required)
                       ,is_allowed= Depends(studentAllowed)):
    return templates.TemplateResponse("summarize_page.html", {"request": request, "summary_": summary})

@router.post("/", response_class=HTMLResponse)
async def summaryNote(request: Request,
                      pdf_file: UploadFile = File(...),
                      is_auth= Depends(auth_required),
                      is_allowed= Depends(studentAllowed)
                      ):

    # Create the directory if it doesn't exist
    directory_path = f"static/TeacherAssignment"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename (prevent issues with slashes or invalid characters)
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")

    # Define file path correctly
    file_location = os.path.join(directory_path, safe_filename)

    # Save the uploaded file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())
    
    api_key = os.getenv("GOOGLE_API_KEY")
    summarizer = SummarizePDF(file_location, api_key)

    # Run the summarization and topic extraction process
    result = await summarizer.run()
    
    result=result.replace("**", "")

    directory = os.path.dirname(file_location)
   
    if os.path.exists(directory):
        # If the directory exists, remove all files in the directory
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    return RedirectResponse(url=f"/summary_note?summary={result}", status_code=303) 

