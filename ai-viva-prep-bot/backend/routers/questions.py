import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.thesis import ThesisDocument
from models.question import GeneratedQuestion
from schemas.question import QuestionResponse
from services.auth_service import get_current_user
from services.question_generation_service import generate_questions

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/generate/{thesis_id}", response_model=list[QuestionResponse])
def generate_questions_for_thesis(
    thesis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == thesis_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    if not thesis.is_analyzed:
        raise HTTPException(status_code=400, detail="Thesis must be analyzed before generating questions")

    existing = db.query(GeneratedQuestion).filter(GeneratedQuestion.document_id == thesis_id).all()
    if existing:
        for q in existing:
            db.delete(q)
        db.commit()

    analysis_json = json.dumps({
        "project_title": thesis.project_title,
        "technologies": json.loads(thesis.technologies_detected) if thesis.technologies_detected else [],
        "methodology": thesis.methodology_detected,
        "sections": json.loads(thesis.sections_detected) if thesis.sections_detected else [],
        "research_questions": json.loads(thesis.research_questions) if thesis.research_questions else [],
        "key_findings": json.loads(thesis.key_findings) if thesis.key_findings else [],
        "limitations": json.loads(thesis.limitations) if thesis.limitations else [],
    }, indent=2)

    questions_data = generate_questions(analysis_json, current_user.preferred_provider)

    if not questions_data:
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

    created = []
    for qd in questions_data:
        q = GeneratedQuestion(
            document_id=thesis_id,
            question_text=qd.get("question", ""),
            difficulty=qd.get("difficulty", "medium"),
            category=qd.get("category", "overview"),
            model_answer=qd.get("model_answer", ""),
            section_reference=qd.get("section_reference"),
        )
        db.add(q)
        created.append(q)

    db.commit()
    for q in created:
        db.refresh(q)

    return created


@router.get("/{thesis_id}", response_model=list[QuestionResponse])
def list_questions(
    thesis_id: int,
    difficulty: str = Query(None),
    category: str = Query(None),
    bookmarked: bool = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == thesis_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    query = db.query(GeneratedQuestion).filter(GeneratedQuestion.document_id == thesis_id)
    if difficulty:
        query = query.filter(GeneratedQuestion.difficulty == difficulty)
    if category:
        query = query.filter(GeneratedQuestion.category == category)
    if bookmarked is not None:
        query = query.filter(GeneratedQuestion.is_bookmarked == bookmarked)

    return query.order_by(GeneratedQuestion.difficulty, GeneratedQuestion.category).all()


@router.put("/{question_id}/bookmark", response_model=QuestionResponse)
def toggle_bookmark(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == question.document_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=403, detail="Access denied")

    question.is_bookmarked = not question.is_bookmarked
    db.commit()
    db.refresh(question)
    return question
