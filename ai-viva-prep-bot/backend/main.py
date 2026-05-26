import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, thesis, questions, viva, reports, settings, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create all tables
from models.user import User
from models.thesis import ThesisDocument
from models.question import GeneratedQuestion
from models.viva_session import VivaSession
from models.session_answer import SessionAnswer

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Viva Prep Bot",
    description="AI-Powered Viva/Defense Preparation Bot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(thesis.router)
app.include_router(questions.router)
app.include_router(viva.router)
app.include_router(reports.router)
app.include_router(settings.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "AI Viva Prep Bot API", "version": "1.0.0", "docs": "/docs"}
