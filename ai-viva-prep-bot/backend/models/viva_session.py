from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class VivaSession(Base):
    __tablename__ = "viva_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("thesis_documents.id"), nullable=False)
    session_type = Column(String(20), nullable=False)  # full_mock | topic_practice | quick_fire
    difficulty_filter = Column(String(10), default="all")  # all | easy | medium | hard
    total_questions = Column(Integer, default=0)
    answered_count = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)
    strong_areas = Column(Text, nullable=True)  # JSON array
    weak_areas = Column(Text, nullable=True)  # JSON array
    study_recommendations = Column(Text, nullable=True)  # JSON array
    status = Column(String(20), default="in_progress")  # in_progress | completed | abandoned
    question_order = Column(Text, nullable=True)  # JSON array of question IDs
    current_question_index = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="viva_sessions")
    document = relationship("ThesisDocument", back_populates="viva_sessions")
    answers = relationship("SessionAnswer", back_populates="session", cascade="all, delete-orphan")
