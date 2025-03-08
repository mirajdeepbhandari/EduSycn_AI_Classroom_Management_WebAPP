import os
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from authentication.authentication import auth_required
from authentication.authorizations import teacherAllowed
from fastapi.templating import Jinja2Templates
from process.pdfProcessor import PDFProcessor
from dotenv import load_dotenv
from graphs.graph import build_Agentic_Graph
from services.AIServices.SlideGenerator import generate_ppt
from datetime import datetime
load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def slideGeN(request: Request,
                      generated: str = None,
                      file_name: str = None,
                       is_auth= Depends(auth_required)
                       ,is_allowed= Depends(teacherAllowed)):
    
    if file_name:
        file_name = file_name.replace(".pdf", ".pptx")
    
    return templates.TemplateResponse("TEACHER/slidegen.html", {"request": request, "generated": generated, "file_name": file_name})

@router.post("/", response_class=HTMLResponse)
async def slideGeN(request: Request,
                      pdf_file: UploadFile = File(...),
                      theme: str = Form(...),
                      is_auth= Depends(auth_required),
                      is_allowed= Depends(teacherAllowed)
                      ):
    

    # Create the directory if it doesn't exist
    directory_path = f"static/SlideContent"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename (prevent issues with slashes or invalid characters)
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Combine the timestamp with the original filename
    new_file_name = f"{current_time}_{safe_filename}"

    # Define file path correctly
    file_location = os.path.join(directory_path, new_file_name)

    # Save the uploaded file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    processor = PDFProcessor(api_key)

    contents = processor.summarize(file_location)

    graph_output = build_Agentic_Graph(contents)
    
    generate_ppt(theme_name=theme, output=graph_output, file_name=new_file_name)

    directory = os.path.dirname(file_location)
   
    if os.path.exists(directory):
        # If the directory exists, remove all files in the directory
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    return RedirectResponse(url=f"/slidegen?generated=yes?&file_name={new_file_name}", status_code=302)



