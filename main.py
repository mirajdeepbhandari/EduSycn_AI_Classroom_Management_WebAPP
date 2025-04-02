from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


from routes import (auth,studentDashboard,classroom,postManagement,
                    listClassMembers,teacherDashboard,assignment,notification,
                    chat,summary,mcq,socketsChat,superAdmin,slidegen,teacherFeedback)



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="ses")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains to access the API (adjust as needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

templates = Jinja2Templates(directory="templates")



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    error = request.session.pop("error", None)
    success = request.session.pop("success", None)
    return templates.TemplateResponse("login.html", {"request": request,"error": error, "success": success})



app.include_router(auth.router, prefix="/auth")
app.include_router(studentDashboard.router, prefix="/student_dashboard")
app.include_router(classroom.router, prefix="/class")
app.include_router(postManagement.router, prefix="/pm")
app.include_router(listClassMembers.router, prefix="/classroom_students")
app.include_router(teacherDashboard.router, prefix="/teacher_dashboard")
app.include_router(assignment.router, prefix="/cw")
app.include_router(notification.router, prefix="/notification")
app.include_router(chat.router, prefix="/chat")
app.include_router(summary.router, prefix="/summary_note")
app.include_router(mcq.router, prefix="/mcq")
app.include_router(socketsChat.router, prefix="/skets")
app.include_router(superAdmin.router, prefix="/sa")
app.include_router(slidegen.router, prefix="/slidegen")
app.include_router(teacherFeedback.router, prefix="/feedbackform")


@app.get("/404", response_class=HTMLResponse)
async def notFound(request: Request):
    return templates.TemplateResponse("404.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8200, log_level="debug")

#### slide gen route ma slide gen ko pdf store garne path need to be change