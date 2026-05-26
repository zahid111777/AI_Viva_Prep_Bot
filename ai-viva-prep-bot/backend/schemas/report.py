from pydantic import BaseModel
from typing import Optional, List


class StudyRecommendation(BaseModel):
    topic: str
    reason: str
    priority: str  # high | medium | low


class ReadinessReportResponse(BaseModel):
    session_id: int
    overall_score: float
    readiness_level: str  # not_ready | needs_work | almost_ready | well_prepared
    strong_areas: List[str]
    weak_areas: List[str]
    study_recommendations: List[StudyRecommendation]
    practice_again_question_ids: List[int]
    examiner_impression: str
    total_questions: int
    answered_count: int
    average_score: float
    session_type: str
    started_at: str
    ended_at: Optional[str] = None
