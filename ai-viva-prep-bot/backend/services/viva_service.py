import json
import logging
import random
from datetime import datetime
from sqlalchemy.orm import Session
from models.question import GeneratedQuestion
from models.viva_session import VivaSession
from models.session_answer import SessionAnswer
from services.scoring_service import score_answer
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

FOLLOW_UP_PROMPT = """The student was asked: {question}
They answered: {student_answer}
The ideal answer was: {model_answer}

Based on their answer:
1. If the answer was vague or incomplete, generate ONE follow-up question that probes deeper into the weak point
2. If the answer was wrong, generate a clarifying question that gives them a chance to correct themselves
3. If the answer was excellent, return null (no follow-up needed)

Return ONLY valid JSON:
{{
  "needs_followup": true,
  "follow_up_question": "..." 
}}

If no follow-up needed:
{{
  "needs_followup": false,
  "follow_up_question": null
}}"""


def create_session(db: Session, user_id: int, document_id: int, session_type: str,
                   difficulty_filter: str = "all", category_filter: str = None) -> VivaSession:
    query = db.query(GeneratedQuestion).filter(GeneratedQuestion.document_id == document_id)

    if difficulty_filter != "all":
        query = query.filter(GeneratedQuestion.difficulty == difficulty_filter)
    if category_filter:
        query = query.filter(GeneratedQuestion.category == category_filter)

    all_questions = query.all()
    if not all_questions:
        raise ValueError("No questions available. Please generate questions first.")

    if session_type == "full_mock":
        selected = _select_full_mock(all_questions)
    elif session_type == "topic_practice":
        selected = all_questions[:20]
        random.shuffle(selected)
    elif session_type == "quick_fire":
        selected = random.sample(all_questions, min(10, len(all_questions)))
    else:
        selected = all_questions[:15]

    question_ids = [q.id for q in selected]

    session = VivaSession(
        user_id=user_id,
        document_id=document_id,
        session_type=session_type,
        difficulty_filter=difficulty_filter,
        total_questions=len(question_ids),
        question_order=json.dumps(question_ids),
        current_question_index=0,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _select_full_mock(questions: list) -> list:
    easy = [q for q in questions if q.difficulty == "easy"]
    medium = [q for q in questions if q.difficulty == "medium"]
    hard = [q for q in questions if q.difficulty == "hard"]
    curveball = [q for q in questions if q.category == "curveball"]

    selected = []
    selected.extend(random.sample(easy, min(5, len(easy))))
    selected.extend(random.sample(medium, min(8, len(medium))))
    selected.extend(random.sample(hard, min(5, len(hard))))

    remaining_curveballs = [q for q in curveball if q not in selected]
    selected.extend(random.sample(remaining_curveballs, min(2, len(remaining_curveballs))))

    random.shuffle(selected)
    return selected


def get_current_question(db: Session, session: VivaSession) -> dict:
    if session.status != "in_progress":
        return None

    question_ids = json.loads(session.question_order)
    if session.current_question_index >= len(question_ids):
        return None

    question_id = question_ids[session.current_question_index]
    question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()
    if not question:
        return None

    return {
        "question_id": question.id,
        "question_text": question.question_text,
        "difficulty": question.difficulty,
        "category": question.category,
        "question_number": session.current_question_index + 1,
        "total_questions": session.total_questions,
    }


def submit_answer(db: Session, session: VivaSession, student_answer: str,
                  preferred_provider: str = "auto") -> dict:
    question_ids = json.loads(session.question_order)
    if session.current_question_index >= len(question_ids):
        raise ValueError("No more questions in this session")

    question_id = question_ids[session.current_question_index]
    question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()

    score_result = score_answer(
        question.question_text, question.model_answer, student_answer, preferred_provider
    )

    follow_up = None
    if session.session_type != "quick_fire":
        follow_up = _generate_follow_up(
            question.question_text, student_answer, question.model_answer, preferred_provider
        )

    answer = SessionAnswer(
        session_id=session.id,
        question_id=question.id,
        student_answer=student_answer,
        score=score_result["score"],
        feedback=score_result["feedback"],
        strengths=json.dumps(score_result.get("strengths", [])),
        weaknesses=json.dumps(score_result.get("weaknesses", [])),
        follow_up_question=follow_up.get("follow_up_question") if follow_up and follow_up.get("needs_followup") else None,
    )
    db.add(answer)

    question.times_attempted += 1
    if question.best_score is None or score_result["score"] > question.best_score:
        question.best_score = score_result["score"]

    session.answered_count += 1
    session.current_question_index += 1

    if session.current_question_index >= len(question_ids):
        _finalize_session(db, session)

    db.commit()
    db.refresh(answer)

    return {
        "answer_id": answer.id,
        "score": score_result["score"],
        "feedback": score_result["feedback"],
        "strengths": score_result.get("strengths", []),
        "weaknesses": score_result.get("weaknesses", []),
        "tip": score_result.get("tip", ""),
        "follow_up_question": answer.follow_up_question,
        "model_answer": question.model_answer,
        "has_next": session.current_question_index < len(question_ids),
    }


def submit_follow_up(db: Session, session: VivaSession, answer_id: int,
                     follow_up_answer: str, preferred_provider: str = "auto") -> dict:
    answer = db.query(SessionAnswer).filter(
        SessionAnswer.id == answer_id, SessionAnswer.session_id == session.id
    ).first()
    if not answer or not answer.follow_up_question:
        raise ValueError("No follow-up question for this answer")

    question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == answer.question_id).first()

    fu_score = score_answer(
        answer.follow_up_question, question.model_answer, follow_up_answer, preferred_provider
    )

    answer.follow_up_answer = follow_up_answer
    answer.follow_up_score = fu_score["score"]
    answer.follow_up_feedback = fu_score["feedback"]
    db.commit()

    return {
        "follow_up_score": fu_score["score"],
        "follow_up_feedback": fu_score["feedback"],
    }


def skip_question(db: Session, session: VivaSession) -> dict:
    question_ids = json.loads(session.question_order)
    if session.current_question_index >= len(question_ids):
        raise ValueError("No more questions")

    question_id = question_ids[session.current_question_index]
    question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()

    answer = SessionAnswer(
        session_id=session.id,
        question_id=question.id,
        student_answer="[SKIPPED]",
        score=0,
        feedback="Question was skipped.",
    )
    db.add(answer)

    session.answered_count += 1
    session.current_question_index += 1

    if session.current_question_index >= len(question_ids):
        _finalize_session(db, session)

    db.commit()
    return {"skipped": True, "has_next": session.current_question_index < len(question_ids)}


def end_session_early(db: Session, session: VivaSession):
    _finalize_session(db, session)
    session.status = "abandoned" if session.answered_count == 0 else "completed"
    db.commit()


def _finalize_session(db: Session, session: VivaSession):
    answers = db.query(SessionAnswer).filter(SessionAnswer.session_id == session.id).all()
    if answers:
        scores = [a.score for a in answers if a.student_answer != "[SKIPPED]"]
        session.overall_score = sum(scores) / len(scores) if scores else 0.0
    session.status = "completed"
    session.ended_at = datetime.utcnow()


def _generate_follow_up(question: str, student_answer: str, model_answer: str,
                        preferred_provider: str = "auto") -> dict:
    prompt = FOLLOW_UP_PROMPT.format(
        question=question,
        student_answer=student_answer,
        model_answer=model_answer,
    )
    try:
        response = llm_service.call_llm(
            "You are a university examiner conducting a viva. Decide if a follow-up is needed. Return ONLY valid JSON.",
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
        return json.loads(response.strip())
    except Exception as e:
        logger.warning(f"Follow-up generation failed: {e}")
        return {"needs_followup": False, "follow_up_question": None}
