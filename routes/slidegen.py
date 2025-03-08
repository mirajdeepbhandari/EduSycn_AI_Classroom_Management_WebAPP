from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import teacherAllowed
from fastapi.templating import Jinja2Templates
import os
from process.pdfProcessor import PDFProcessor
from dotenv import load_dotenv
from graphs.graph import build_Agentic_Graph
from services.AIServices.SlideGenerator import generate_ppt
load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def slideGeN(request: Request,
                      summary: str = None,
                       is_auth= Depends(auth_required)
                       ,is_allowed= Depends(teacherAllowed)):
    return templates.TemplateResponse("TEACHER/slidegen.html", {"request": request, "summary_": summary})

@router.post("/", response_class=HTMLResponse)
async def slideGeN(request: Request,
                      pdf_file: UploadFile = File(...),
                      theme: str = Form(...),
                      is_auth= Depends(auth_required),
                      is_allowed= Depends(teacherAllowed)
                      ):
    

    print(pdf_file.filename, theme)

    # Create the directory if it doesn't exist
    directory_path = f"static/SlideContent"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename (prevent issues with slashes or invalid characters)
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")

    # Define file path correctly
    file_location = os.path.join(directory_path, safe_filename)

    # Save the uploaded file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
     
    summarizer = PDFProcessor(api_key)

    contents = summarizer.summarize(file_location)

    graph_output = build_Agentic_Graph(contents)
    
    generate_ppt(theme_name=theme, output=graph_output)

    directory = os.path.dirname(file_location)
   
    if os.path.exists(directory):
        # If the directory exists, remove all files in the directory
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    return RedirectResponse(url=f"/slidegen", status_code=303) 

