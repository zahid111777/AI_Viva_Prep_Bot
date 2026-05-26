from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("thesis_documents.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    difficulty = Column(String(10), nullable=False)  # easy | medium | hard
    category = Column(String(20), nullable=False)
    model_answer = Column(Text, nullable=False)
    section_reference = Column(String(255), nullable=True)
    is_bookmarked = Column(Boolean, default=False)
    times_attempted = Column(Integer, default=0)
    best_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("ThesisDocument", back_populates="questions")
    session_answers = relationship("SessionAnswer", back_populates="question", cascade="all, delete-orphan")
