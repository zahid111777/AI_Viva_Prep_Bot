from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.user import User
from models.thesis import ThesisDocument
from models.question import GeneratedQuestion
from models.viva_session import VivaSession
from schemas.user import UserResponse
from services.auth_service import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    total_theses = db.query(func.count(ThesisDocument.id)).scalar()
    total_questions = db.query(func.count(GeneratedQuestion.id)).scalar()
    total_sessions = db.query(func.count(VivaSession.id)).scalar()
    avg_score = db.query(func.avg(VivaSession.overall_score)).filter(
        VivaSession.overall_score.isnot(None)
    ).scalar()

    return {
        "total_users": total_users,
        "total_theses": total_theses,
        "total_questions": total_questions,
        "total_sessions": total_sessions,
        "average_readiness_score": round(avg_score, 2) if avg_score else 0,
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'deactivated' if not user.is_active else 'activated'}", "is_active": user.is_active}
