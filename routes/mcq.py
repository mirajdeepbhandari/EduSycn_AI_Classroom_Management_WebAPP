from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from authentication.authentication import auth_required
from authentication.authorizations import studentAllowed, teacherAllowed
from services.AIServices.McqGenerator import PDFMCQGenerator
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from models.database import McqMarks, Student, get_db
from fastapi.templating import Jinja2Templates
import os
import json
from utils.utils import parse_json, parse_questions
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/generatemcq", response_class=HTMLResponse)
async def GenerateMcqPage(
    request: Request,
    subject_id: str,
    subject: str,
    class_id: str,
    mcq_output: str = None,
    db: Session = Depends(get_db),
    is_auth= Depends(auth_required),
    is_allowed= Depends(teacherAllowed),
):
    file_path = "jsonDB/mcq_data.json"
    mcq_output_json = None

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Load or create JSON file
        if not os.path.exists(file_path):
            mcq_data = {}
            with open(file_path, 'w') as json_file:
                json.dump(mcq_data, json_file, indent=4)
        else:
            with open(file_path, 'r') as json_file:
                try:
                    mcq_data = json.load(json_file)
                except json.JSONDecodeError:
                    mcq_data = {}

        # Extract MCQ questions safely
        mcq_json = (
            mcq_data
            .get(f"class_{class_id}", {})
            .get("subjects", {})
            .get(subject_id, {})
            .get("questions", {})
        )

        if mcq_json:
            mcq_output_json = parse_json(mcq_json).strip().replace("*", "")

    except Exception as e:
        print(f"An error occurred while handling JSON: {e}")

    try:
        exam_marks = (
            db.query(McqMarks.student_id, McqMarks.user_name, McqMarks.marks, McqMarks.percentage)
            .filter(McqMarks.class_id == class_id, McqMarks.subject_id == subject_id)
            .all()
        )

    except Exception as e:
        print(f"Database error: {e}")
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "TEACHER/generate_mcq.html",
        {
            "request": request,
            "subject_id": subject_id,
            "subject": subject,
            "class_id": class_id,
            "textout_mcq": mcq_output,
            "mcq_from_json": mcq_output_json,
            "examMarks": exam_marks
        }
    )


# @router.post("/generatemcq", response_class=HTMLResponse)
# async def GenerateMcqPage(
#     pdf_file: UploadFile = File(...),
#     subject_id: str = Form(...),
#     subject: str = Form(...),
#     class_id: str = Form(...),
#     is_auth= Depends(auth_required),
#     is_allowed= Depends(teacherAllowed),
# ):
#     # Create the directory if it doesn't exist
#     directory_path = f"static/PDFProcessing/{class_id}/{subject_id}/{subject}"
#     os.makedirs(directory_path, exist_ok=True)

#     # Ensure a clean filename (prevent issues with slashes or invalid characters)
#     safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")

#     # Define file path correctly
#     file_location = os.path.join(directory_path, safe_filename)

#     # Save the uploaded file
#     with open(file_location, "wb") as file:
#         file.write(await pdf_file.read())

#     # Process the PDF and generate MCQs
#     api_key = os.getenv("GOOGLE_API_KEY")

#     mcq_generator = PDFMCQGenerator(file_location, api_key)
#     textout = mcq_generator.run()

#     # Delete the uploaded PDF file
#     directory = os.path.dirname(file_location )
#     print(directory)
#     if os.path.exists(directory):
#         # If the directory exists, remove all files in the directory
#         for file in os.listdir(directory):
#             file_path = os.path.join(directory, file)
#             if os.path.isfile(file_path):
#                 os.remove(file_path)

    
#     # Redirect to GET route with necessary data
#     query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}&mcq_output={textout}"
#     return RedirectResponse(url=f"/mcq/generatemcq{query_params}", status_code=303)




@router.post("/generatemcq", response_class=HTMLResponse)
async def GenerateMcqPage(
    pdf_file: UploadFile = File(...),
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    is_auth= Depends(auth_required),
    is_allowed= Depends(teacherAllowed),
):
    # Create the directory if it doesn't exist
    directory_path = f"static/PDFProcessing/{class_id}/{subject_id}/{subject}"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")
    file_location = os.path.join(directory_path, safe_filename)

    # Save uploaded PDF file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())

    # Generate MCQs from PDF
    api_key = os.getenv("GOOGLE_API_KEY")
    mcq_generator = PDFMCQGenerator(file_location, api_key)
    textout = await mcq_generator.run()  # <-- ✅ AWAIT the async call

    # Clean up uploaded file
    directory = os.path.dirname(file_location)
    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # Redirect with query params
    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}&mcq_output={textout}"
    return RedirectResponse(url=f"/mcq/generatemcq{query_params}", status_code=303)


@router.post("/publishmcq", response_class=HTMLResponse)
async def publishMcq(request: Request,
                      subject_id: str = Form(...),
                      subject: str = Form(...),
                      class_id: str = Form(...),
                      mcq_text: str = Form(...),
                      is_auth= Depends(auth_required),
                      is_allowed= Depends(teacherAllowed)):

    # Assuming parse_questions is a function that returns questions data
    ans = parse_questions(mcq_text)
    
    # Define the file path where you want to save the JSON data
    file_path = 'jsonDB/mcq_data.json'

    # Try to read the existing data from the file
    try:
        with open(file_path, 'r') as json_file:
            mcq_data = json.load(json_file)
    except FileNotFoundError:
        # If file doesn't exist, initialize an empty structure
        mcq_data = {}

    # Ensure the class exists in the data
    if f"class_{class_id}" not in mcq_data:
        mcq_data[f"class_{class_id}"] = {
            "subjects": {}
        }

    # Check if the subject already exists under the class
    if subject_id not in mcq_data[f"class_{class_id}"]["subjects"]:
        mcq_data[f"class_{class_id}"]["subjects"][subject_id] = {
            "questions": ans
        }
    else:
        # If subject exists, append the questions to the existing ones
        mcq_data[f"class_{class_id}"]["subjects"][subject_id]["questions"].update(ans)

    # Save the updated JSON data back to the file
    with open(file_path, 'w') as json_file:
        json.dump(mcq_data, json_file, indent=2)

    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}"
    return RedirectResponse(url=f"/mcq/generatemcq{query_params}", status_code=303) 


@router.post("/deletemcq", response_class=HTMLResponse)
async def deleteMcq(request: Request,
                     subject_id: str = Form(...),
                     subject: str = Form(...),
                     class_id: str = Form(...),
                     db: Session = Depends(get_db),
                     is_auth= Depends(auth_required),
                     is_allowed= Depends(teacherAllowed)):

    try:
        # Open the JSON file
        with open('jsonDB/mcq_data.json', 'r') as json_file:
            mcq_data = json.load(json_file)

        # Check if the specified class and subject exist
        class_key = f"class_{class_id}"
        if class_key in mcq_data and "subjects" in mcq_data[class_key]:
            subjects = mcq_data[class_key]["subjects"]
            if subject_id in subjects:
                # Remove the subject
                subjects.pop(subject_id)
                # Save the updated JSON back to the file
                with open('jsonDB/mcq_data.json', 'w') as json_file:
                    json.dump(mcq_data, json_file, indent=2)
            else:
                message = f"Subject with ID {subject_id} does not exist."
        else:
            message = f"Class {class_id} or subjects not found."

    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
    
    try:
       db.query(McqMarks).filter(McqMarks.class_id == class_id, McqMarks.subject_id == subject_id).delete()
       db.commit()    
    except Exception as e:
        print(e)
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}"
    return RedirectResponse(url=f"/mcq/generatemcq{query_params}", status_code=303) 


@router.get("/mcqpage", response_class=HTMLResponse)
async def McqPageStudent(request: Request,
                         subject_id: str,
                         subject: str,
                         class_id: str,
                         db: Session = Depends(get_db),
                         is_auth= Depends(auth_required),
                         is_allowed= Depends(studentAllowed)):
    
    try:
        studentID = db.query(Student.student_id).filter(Student.user_id==request.session.get('user_id')).first()
        studentID=studentID[0]
        is_exam_taken = db.query(McqMarks.is_taken).filter(McqMarks.class_id == class_id,McqMarks.subject_id == subject_id,McqMarks.student_id == studentID).first()
        if is_exam_taken:
            is_exam_taken = is_exam_taken[0]
            if is_exam_taken == 'yes':
                return RedirectResponse(url="/mcq/exam_submission_status", status_code=303)
    except Exception as e:
        print(e)
        request.session["error"] = "Something Went Wrong on Server !!!"
        return RedirectResponse(url="/", status_code=303)

    
    fullmarks=""
    passmarks=""
    ques=None

    student_ = request.session.get('user_name')
    studentid_ = request.session.get('user_id')
    
    try:
        # Open the JSON file
        with open('jsonDB/mcq_data.json', 'r') as json_file:
            mcq_data = json.load(json_file)

        
        mcq_json = mcq_data.get(f"class_{class_id}", {}).get("subjects", {}).get(subject_id, {}).get("questions", {})
       
        if len(mcq_json) == 0:
            ques=None
        
        else:

            fullmarks= len(mcq_json)
            passmarks= int((len(mcq_json)/2)-2)
            ques= mcq_json
      


    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
    

    return templates.TemplateResponse("mcqpage.html", {"request": request,
                                                       "questions":ques,
                                                       "fullmark":fullmarks,
                                                       "passmark":passmarks, 
                                                       "subject_id": subject_id,
                                                       "subject": subject,
                                                        "class_id": class_id,
                                                        "studentname": student_,
                                                        "studentid": studentid_})


@router.post("/submit_mcq")
async def submitMcq(request: Request,
                        subject_id: str = Form(...),
                        subject: str = Form(...),
                        class_id: str = Form(...),
                        student_id: str = Form(...),
                        student_name: str = Form(...),
                        db: Session = Depends(get_db),
                        is_auth= Depends(auth_required),
                        is_allowed= Depends(studentAllowed)):
    
    form_data = await request.form() 
    answers = dict(form_data)  # Convert to dictionary

    with open("jsonDB/mcq_data.json", 'r') as json_file:
            mcq_data = json.load(json_file)
            
    # Validate answers
    if (subjects := mcq_data.get(f"class_{class_id}", {}).get("subjects")) and subject_id in subjects:
        correct_count = 0
        total_questions = len(answers)

        for q_num, user_answer in answers.items():
            question_id = q_num.replace("question", "")
            correct_answer = subjects[subject_id]["questions"].get(question_id, {}).get("correct_answer")

            if correct_answer and user_answer == correct_answer:
                correct_count += 1

        accuracy = (correct_count / total_questions) * 100

    try:
       
        studentID = db.query(Student.student_id).filter_by(user_id=student_id).first()
        
        marks = McqMarks(student_id=studentID[0],
                        user_name=student_name,
                        class_id=class_id,
                        subject_id=subject_id,
                        marks=correct_count,
                        percentage=accuracy,
                        is_taken="yes")
        
        db.add(marks)
        db.flush() 
        db.refresh(marks)  
        db.commit()
        
    except Exception as e:
        return {"error": str(e)}

    return templates.TemplateResponse("thankyoupage.html", {"request": request, "subject_name": subject})


@router.get("/exam_submission_status", response_class=HTMLResponse)
async def examSubmissionStatus(request: Request, is_auth= Depends(auth_required),
                                is_allowed= Depends(studentAllowed)):
    return templates.TemplateResponse("examalreadysubmission.html", {"request": request})