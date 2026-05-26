import json
import logging
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

SCORING_PROMPT = """You are a strict but fair university examiner. Score this viva answer.

Question: {question}
Model answer (ideal): {model_answer}
Student's answer: {student_answer}

Score from 0-10:
- 0-2: Completely wrong or "I don't know"
- 3-4: Vaguely correct but missing key points
- 5-6: Partially correct, shows some understanding
- 7-8: Good answer, covers most key points
- 9-10: Excellent, comprehensive, shows deep understanding

Return ONLY valid JSON:
{{
  "score": 0,
  "feedback": "Specific feedback on what was good and what was missing",
  "strengths": ["What the student got right"],
  "weaknesses": ["What was missing or wrong"],
  "tip": "One specific tip to improve this answer"
}}"""


def score_answer(question: str, model_answer: str, student_answer: str, preferred_provider: str = "auto") -> dict:
    prompt = SCORING_PROMPT.format(
        question=question,
        model_answer=model_answer,
        student_answer=student_answer,
    )

    response = llm_service.call_llm(
        "You are a university viva examiner. Score answers accurately and provide constructive feedback. Return ONLY valid JSON.",
        prompt,
        preferred=preferred_provider,
    )

    try:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        result = json.loads(response.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse scoring JSON: {response[:200]}")
        result = {
            "score": 5,
            "feedback": "Unable to parse AI scoring. Default score assigned.",
            "strengths": [],
            "weaknesses": ["Could not evaluate response properly"],
            "tip": "Please try answering again.",
        }

    result["score"] = max(0, min(10, int(result.get("score", 5))))
    return result
