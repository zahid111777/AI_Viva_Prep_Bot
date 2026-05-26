from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuestionResponse(BaseModel):
    id: int
    document_id: int
    question_text: str
    difficulty: str
    category: str
    model_answer: str
    section_reference: Optional[str] = None
    is_bookmarked: bool
    times_attempted: int
    best_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionBookmarkToggle(BaseModel):
    is_bookmarked: bool
