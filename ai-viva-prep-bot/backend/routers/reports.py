from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.viva_session import VivaSession
from schemas.report import ReadinessReportResponse
from services.auth_service import get_current_user
from services.report_service import generate_report, generate_study_guide_pdf, generate_questions_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{session_id}", response_model=ReadinessReportResponse)
def get_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "in_progress":
        raise HTTPException(status_code=400, detail="Session is still in progress")

    report = generate_report(db, session, current_user.preferred_provider)
    return report


@router.get("/{session_id}/pdf")
def download_study_guide_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    buffer = generate_study_guide_pdf(db, session)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=study_guide_session_{session_id}.pdf"},
    )


@router.get("/{session_id}/questions-pdf")
def download_questions_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(VivaSession).filter(
        VivaSession.id == session_id, VivaSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    buffer = generate_questions_pdf(db, session.document_id)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=questions_session_{session_id}.pdf"},
    )
