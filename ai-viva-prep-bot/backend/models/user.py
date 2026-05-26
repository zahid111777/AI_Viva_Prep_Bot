from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(10), default="user")  # user | admin
    university = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    preferred_provider = Column(String(20), default="auto")  # auto|groq|openrouter|openai|gemini
    encrypted_groq_key = Column(Text, nullable=True)
    encrypted_openrouter_key = Column(Text, nullable=True)
    encrypted_openai_key = Column(Text, nullable=True)
    encrypted_gemini_key = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    theses = relationship("ThesisDocument", back_populates="user", cascade="all, delete-orphan")
    viva_sessions = relationship("VivaSession", back_populates="user", cascade="all, delete-orphan")
