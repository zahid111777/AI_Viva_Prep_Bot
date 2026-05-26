from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SectionInfo(BaseModel):
    name: str
    detected: bool


class ThesisResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    project_title: Optional[str] = None
    technologies_detected: Optional[List[str]] = None
    methodology_detected: Optional[str] = None
    sections_detected: Optional[List[SectionInfo]] = None
    research_questions: Optional[List[str]] = None
    key_findings: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    word_count: int
    is_analyzed: bool
    upload_date: datetime

    class Config:
        from_attributes = True


class ThesisListResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    project_title: Optional[str] = None
    word_count: int
    is_analyzed: bool
    upload_date: datetime

    class Config:
        from_attributes = True
