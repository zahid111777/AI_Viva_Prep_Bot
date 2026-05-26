from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class SessionAnswer(Base):
    __tablename__ = "session_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("viva_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("generated_questions.id"), nullable=False)
    student_answer = Column(Text, nullable=False)
    score = Column(Integer, default=0)
    feedback = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)  # JSON array
    weaknesses = Column(Text, nullable=True)  # JSON array
    follow_up_question = Column(Text, nullable=True)
    follow_up_answer = Column(Text, nullable=True)
    follow_up_score = Column(Integer, nullable=True)
    follow_up_feedback = Column(Text, nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VivaSession", back_populates="answers")
    question = relationship("GeneratedQuestion", back_populates="session_answers")
