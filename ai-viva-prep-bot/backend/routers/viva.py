import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.viva_session import VivaSession
from schemas.session import VivaStartRequest, VivaSessionResponse, VivaSessionDetailResponse, CurrentQuestionResponse
from schemas.answer import AnswerSubmit, FollowUpSubmit
from services.auth_service import get_current_user
from services import viva_service

router = APIRouter(prefix="/viva", tags=["Viva Sessions"])


@router.post("/start", response_model=VivaSessionResponse, status_code=201)
def start_viva(
    data: VivaStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session = viva_service.create_session(
            db, current_user.id, data.document_id, data.session_type,
            data.difficulty_filter, data.category_filter,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=list[VivaSessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(VivaSession).filter(
        VivaSession.user_id == current_user.id
    ).order_by(VivaSession.started_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=VivaSessionDetailResponse)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return VivaSessionDetailResponse(
        id=session.id,
        document_id=session.document_id,
        session_type=session.session_type,
        difficulty_filter=session.difficulty_filter,
        total_questions=session.total_questions,
        answered_count=session.answered_count,
        overall_score=session.overall_score,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        strong_areas=json.loads(session.strong_areas) if session.strong_areas else None,
        weak_areas=json.loads(session.weak_areas) if session.weak_areas else None,
        study_recommendations=json.loads(session.study_recommendations) if session.study_recommendations else None,
        current_question_index=session.current_question_index,
    )


@router.get("/sessions/{session_id}/current-question", response_model=CurrentQuestionResponse)
def get_current_question(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question = viva_service.get_current_question(db, session)
    if not question:
        raise HTTPException(status_code=404, detail="No more questions or session completed")
    return question


@router.post("/sessions/{session_id}/answer")
def submit_answer(
    session_id: int,
    data: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")
    if len(data.answer.strip()) < 1:
        raise HTTPException(status_code=400, detail="Please write your answer before submitting.")

    try:
        result = viva_service.submit_answer(db, session, data.answer, current_user.preferred_provider)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/followup")
def submit_followup(
    session_id: int,
    data: FollowUpSubmit,
    answer_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not answer_id:
        from models.session_answer import SessionAnswer
        last_answer = db.query(SessionAnswer).filter(
            SessionAnswer.session_id == session_id
        ).order_by(SessionAnswer.id.desc()).first()
        if last_answer:
            answer_id = last_answer.id

    try:
        result = viva_service.submit_follow_up(db, session, answer_id, data.answer, current_user.preferred_provider)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/skip")
def skip_question(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    try:
        return viva_service.skip_question(db, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/end")
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    viva_service.end_session_early(db, session)
    return {"message": "Session ended", "status": session.status}
