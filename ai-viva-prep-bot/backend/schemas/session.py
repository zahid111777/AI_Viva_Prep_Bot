from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VivaStartRequest(BaseModel):
    document_id: int
    session_type: str  # full_mock | topic_practice | quick_fire
    difficulty_filter: str = "all"  # all | easy | medium | hard
    category_filter: Optional[str] = None  # for topic_practice


class VivaSessionResponse(BaseModel):
    id: int
    document_id: int
    session_type: str
    difficulty_filter: str
    total_questions: int
    answered_count: int
    overall_score: Optional[float] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VivaSessionDetailResponse(VivaSessionResponse):
    strong_areas: Optional[List[str]] = None
    weak_areas: Optional[List[str]] = None
    study_recommendations: Optional[List[str]] = None
    current_question_index: int = 0


class CurrentQuestionResponse(BaseModel):
    question_id: int
    question_text: str
    difficulty: str
    category: str
    question_number: int
    total_questions: int
