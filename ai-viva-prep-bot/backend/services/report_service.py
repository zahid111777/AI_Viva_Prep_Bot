import json
import logging
import os
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from models.viva_session import VivaSession
from models.session_answer import SessionAnswer
from models.question import GeneratedQuestion
from models.thesis import ThesisDocument
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

REPORT_PROMPT = """Based on this viva session data, generate a readiness assessment.

Session results:
{session_data}

Thesis topics:
{thesis_data}

Return ONLY valid JSON:
{{
  "overall_score": 72,
  "readiness_level": "not_ready|needs_work|almost_ready|well_prepared",
  "strong_areas": ["Topics the student knows well"],
  "weak_areas": ["Topics that need more preparation"],
  "study_recommendations": [
    {{"topic": "...", "reason": "...", "priority": "high|medium|low"}}
  ],
  "practice_again_questions": [1, 2, 3],
  "examiner_impression": "A 2-3 sentence summary of how an examiner would perceive this student's preparedness"
}}"""


def generate_report(db: Session, session: VivaSession, preferred_provider: str = "auto") -> dict:
    answers = db.query(SessionAnswer).filter(SessionAnswer.session_id == session.id).all()
    document = db.query(ThesisDocument).filter(ThesisDocument.id == session.document_id).first()

    session_data = []
    for a in answers:
        q = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == a.question_id).first()
        session_data.append({
            "question": q.question_text if q else "Unknown",
            "difficulty": q.difficulty if q else "unknown",
            "category": q.category if q else "unknown",
            "student_answer": a.student_answer,
            "score": a.score,
            "feedback": a.feedback,
        })

    thesis_data = {
        "project_title": document.project_title if document else "Unknown",
        "technologies": json.loads(document.technologies_detected) if document and document.technologies_detected else [],
        "methodology": document.methodology_detected if document else "unknown",
    }

    prompt = REPORT_PROMPT.format(
        session_data=json.dumps(session_data, indent=2),
        thesis_data=json.dumps(thesis_data, indent=2),
    )

    try:
        response = llm_service.call_llm(
            "You are an academic assessment expert. Generate a viva readiness report. Return ONLY valid JSON.",
            prompt,
            preferred=preferred_provider,
        )
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        report = json.loads(response.strip())
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        scores = [a.score for a in answers if a.student_answer != "[SKIPPED]"]
        avg = sum(scores) / len(scores) * 10 if scores else 0
        report = {
            "overall_score": avg,
            "readiness_level": "needs_work",
            "strong_areas": [],
            "weak_areas": [],
            "study_recommendations": [],
            "practice_again_questions": [a.question_id for a in answers if a.score < 5],
            "examiner_impression": "Unable to generate detailed assessment. Please review your scores.",
        }

    session.strong_areas = json.dumps(report.get("strong_areas", []))
    session.weak_areas = json.dumps(report.get("weak_areas", []))
    session.study_recommendations = json.dumps(report.get("study_recommendations", []))
    db.commit()

    scores = [a.score for a in answers if a.student_answer != "[SKIPPED]"]
    return {
        "session_id": session.id,
        "overall_score": report.get("overall_score", 0),
        "readiness_level": report.get("readiness_level", "needs_work"),
        "strong_areas": report.get("strong_areas", []),
        "weak_areas": report.get("weak_areas", []),
        "study_recommendations": report.get("study_recommendations", []),
        "practice_again_question_ids": report.get("practice_again_questions", []),
        "examiner_impression": report.get("examiner_impression", ""),
        "total_questions": session.total_questions,
        "answered_count": session.answered_count,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "session_type": session.session_type,
        "started_at": session.started_at.isoformat() if session.started_at else "",
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }


def generate_study_guide_pdf(db: Session, session: VivaSession) -> BytesIO:
    answers = db.query(SessionAnswer).filter(SessionAnswer.session_id == session.id).all()
    document = db.query(ThesisDocument).filter(ThesisDocument.id == session.document_id).first()
    project_title = document.project_title if document else "Thesis"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=22, spaceAfter=20, textColor=colors.HexColor("#7C3AED"))
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#1E293B"), spaceAfter=10)
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"], fontSize=11, spaceAfter=8)

    story.append(Paragraph(f"Viva Preparation Study Guide", title_style))
    story.append(Paragraph(f"{project_title}", heading_style))
    story.append(Spacer(1, 0.3 * inch))

    if session.overall_score is not None:
        score_text = f"Overall Score: {session.overall_score:.1f}/10"
        story.append(Paragraph(score_text, heading_style))
    story.append(Spacer(1, 0.3 * inch))

    if session.weak_areas:
        weak = json.loads(session.weak_areas)
        if weak:
            story.append(Paragraph("Areas to Study", heading_style))
            for area in weak:
                story.append(Paragraph(f"• {area}", body_style))
            story.append(Spacer(1, 0.2 * inch))

    if session.study_recommendations:
        recs = json.loads(session.study_recommendations)
        if recs:
            story.append(Paragraph("Study Recommendations", heading_style))
            for rec in recs:
                if isinstance(rec, dict):
                    story.append(Paragraph(f"• [{rec.get('priority', 'medium').upper()}] {rec.get('topic', '')} — {rec.get('reason', '')}", body_style))
                else:
                    story.append(Paragraph(f"• {rec}", body_style))
            story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Questions & Model Answers", title_style))
    story.append(Spacer(1, 0.2 * inch))

    for i, a in enumerate(answers, 1):
        q = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == a.question_id).first()
        if not q:
            continue

        diff_color = {"easy": "#22C55E", "medium": "#EAB308", "hard": "#EF4444"}.get(q.difficulty, "#666")
        story.append(Paragraph(
            f"<b>Q{i}.</b> [{q.difficulty.upper()}] {q.question_text}",
            ParagraphStyle("Q", parent=body_style, textColor=colors.HexColor("#1E293B"), fontSize=11, spaceAfter=4)
        ))

        score_color = "#22C55E" if a.score >= 8 else "#EAB308" if a.score >= 5 else "#EF4444"
        story.append(Paragraph(
            f"<b>Your Score:</b> <font color='{score_color}'>{a.score}/10</font>",
            body_style
        ))

        story.append(Paragraph(f"<b>Model Answer:</b> {q.model_answer}", body_style))

        if a.feedback:
            story.append(Paragraph(f"<b>Feedback:</b> {a.feedback}", body_style))

        story.append(Spacer(1, 0.15 * inch))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Generated by AI Viva Prep Bot", ParagraphStyle("Footer", parent=body_style, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_questions_pdf(db: Session, document_id: int) -> BytesIO:
    questions = db.query(GeneratedQuestion).filter(
        GeneratedQuestion.document_id == document_id
    ).order_by(GeneratedQuestion.difficulty, GeneratedQuestion.category).all()

    document = db.query(ThesisDocument).filter(ThesisDocument.id == document_id).first()
    project_title = document.project_title if document else "Thesis"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=22, spaceAfter=20, textColor=colors.HexColor("#7C3AED"))
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#1E293B"), spaceAfter=10)
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"], fontSize=11, spaceAfter=8)

    story.append(Paragraph("Viva Questions & Model Answers", title_style))
    story.append(Paragraph(project_title, heading_style))
    story.append(Paragraph(f"Total Questions: {len(questions)}", body_style))
    story.append(Spacer(1, 0.3 * inch))

    current_difficulty = None
    for i, q in enumerate(questions, 1):
        if q.difficulty != current_difficulty:
            current_difficulty = q.difficulty
            diff_label = {"easy": "Easy Questions", "medium": "Medium Questions", "hard": "Hard Questions"}.get(current_difficulty, current_difficulty)
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(diff_label, heading_style))

        story.append(Paragraph(f"<b>Q{i}.</b> [{q.category}] {q.question_text}", body_style))
        story.append(Paragraph(f"<b>Model Answer:</b> {q.model_answer}", body_style))
        story.append(Spacer(1, 0.1 * inch))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Generated by AI Viva Prep Bot", ParagraphStyle("Footer", parent=body_style, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer
