import os
import json
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.thesis import ThesisDocument
from models.question import GeneratedQuestion
from models.viva_session import VivaSession
from schemas.thesis import ThesisResponse, ThesisListResponse
from services.auth_service import get_current_user
from services.extraction_service import extract_text, MAX_FILE_SIZE
from services.thesis_analysis_service import analyze_thesis

router = APIRouter(prefix="/thesis", tags=["Thesis"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ThesisResponse, status_code=201)
async def upload_thesis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Accepted formats: PDF, DOCX.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit.")

    safe_filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        extraction = extract_text(file_path, ext)
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=str(e))

    if extraction["word_count"] < 500:
        os.remove(file_path)
        raise HTTPException(
            status_code=422,
            detail="Document appears too short for meaningful analysis. Please upload your complete thesis.",
        )

    thesis = ThesisDocument(
        user_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        extracted_text=extraction["text"],
        word_count=extraction["word_count"],
    )
    db.add(thesis)
    db.commit()
    db.refresh(thesis)

    try:
        text_for_analysis = extraction["text"]
        if extraction["word_count"] > 50000:
            words = text_for_analysis.split()
            text_for_analysis = " ".join(words[:30000])

        analysis = analyze_thesis(text_for_analysis, current_user.preferred_provider)

        thesis.project_title = analysis.get("project_title")
        thesis.technologies_detected = json.dumps(analysis.get("technologies", []))
        thesis.methodology_detected = analysis.get("methodology")
        thesis.sections_detected = json.dumps(analysis.get("sections", []))
        thesis.research_questions = json.dumps(analysis.get("research_questions", []))
        thesis.key_findings = json.dumps(analysis.get("key_findings", []))
        thesis.limitations = json.dumps(analysis.get("limitations", []))
        thesis.is_analyzed = True
        db.commit()
        db.refresh(thesis)
    except Exception as e:
        pass  # Thesis saved, analysis can be retried

    return _thesis_to_response(thesis)


@router.get("", response_model=list[ThesisListResponse])
def list_theses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    theses = db.query(ThesisDocument).filter(ThesisDocument.user_id == current_user.id).order_by(ThesisDocument.upload_date.desc()).all()
    return theses


@router.get("/{thesis_id}", response_model=ThesisResponse)
def get_thesis(thesis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == thesis_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return _thesis_to_response(thesis)


@router.delete("/{thesis_id}", status_code=204)
def delete_thesis(thesis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == thesis_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{thesis.filename}")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(thesis)
    db.commit()


@router.post("/{thesis_id}/reanalyze", response_model=ThesisResponse)
def reanalyze_thesis(thesis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    thesis = db.query(ThesisDocument).filter(
        ThesisDocument.id == thesis_id, ThesisDocument.user_id == current_user.id
    ).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")

    try:
        analysis = analyze_thesis(thesis.extracted_text, current_user.preferred_provider)
        thesis.project_title = analysis.get("project_title")
        thesis.technologies_detected = json.dumps(analysis.get("technologies", []))
        thesis.methodology_detected = analysis.get("methodology")
        thesis.sections_detected = json.dumps(analysis.get("sections", []))
        thesis.research_questions = json.dumps(analysis.get("research_questions", []))
        thesis.key_findings = json.dumps(analysis.get("key_findings", []))
        thesis.limitations = json.dumps(analysis.get("limitations", []))
        thesis.is_analyzed = True
        db.commit()
        db.refresh(thesis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return _thesis_to_response(thesis)


def _thesis_to_response(thesis: ThesisDocument) -> ThesisResponse:
    return ThesisResponse(
        id=thesis.id,
        filename=thesis.filename,
        file_type=thesis.file_type,
        project_title=thesis.project_title,
        technologies_detected=json.loads(thesis.technologies_detected) if thesis.technologies_detected else None,
        methodology_detected=thesis.methodology_detected,
        sections_detected=[
            {"name": s.get("name", ""), "detected": s.get("detected", False)}
            for s in json.loads(thesis.sections_detected)
        ] if thesis.sections_detected else None,
        research_questions=json.loads(thesis.research_questions) if thesis.research_questions else None,
        key_findings=json.loads(thesis.key_findings) if thesis.key_findings else None,
        limitations=json.loads(thesis.limitations) if thesis.limitations else None,
        word_count=thesis.word_count,
        is_analyzed=thesis.is_analyzed,
        upload_date=thesis.upload_date,
    )
