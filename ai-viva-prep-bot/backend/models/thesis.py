from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class ThesisDocument(Base):
    __tablename__ = "thesis_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf | docx
    extracted_text = Column(Text, nullable=True)
    project_title = Column(String(500), nullable=True)
    technologies_detected = Column(Text, nullable=True)  # JSON array
    methodology_detected = Column(String(100), nullable=True)
    sections_detected = Column(Text, nullable=True)  # JSON array
    research_questions = Column(Text, nullable=True)  # JSON array
    key_findings = Column(Text, nullable=True)  # JSON array
    limitations = Column(Text, nullable=True)  # JSON array
    word_count = Column(Integer, default=0)
    is_analyzed = Column(Boolean, default=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="theses")
    questions = relationship("GeneratedQuestion", back_populates="document", cascade="all, delete-orphan")
    viva_sessions = relationship("VivaSession", back_populates="document", cascade="all, delete-orphan")
