from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AnswerSubmit(BaseModel):
    answer: str


class FollowUpSubmit(BaseModel):
    answer: str


class AnswerScoreResponse(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    tip: str


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    student_answer: str
    score: int
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    follow_up_question: Optional[str] = None
    follow_up_answer: Optional[str] = None
    follow_up_score: Optional[int] = None
    follow_up_feedback: Optional[str] = None
    answered_at: datetime

    class Config:
        from_attributes = True


class AnswerWithQuestionResponse(AnswerResponse):
    question_text: str
    difficulty: str
    category: str
    model_answer: str
