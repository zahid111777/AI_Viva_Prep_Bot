import json
import logging
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

EASY_PROMPT = """You are a university examiner preparing viva questions. Based on this thesis, generate 15 EASY questions that test basic understanding.

These should be questions any student who actually wrote the thesis should answer confidently:
- What is the project about?
- Why did you choose this topic?
- What are the main technologies used?
- Basic "explain this term" questions

For each question return:
{
  "question": "...",
  "difficulty": "easy",
  "category": "overview|technical|methodology|literature|results|ethics|scalability|curveball",
  "model_answer": "The ideal 3-5 sentence answer an examiner would want to hear",
  "section_reference": "Which thesis section this relates to"
}

Return ONLY a valid JSON array of 15 question objects. No markdown, no extra text."""

MEDIUM_PROMPT = """You are a university examiner. Generate 20 MEDIUM difficulty viva questions that test technical depth and design decisions:
- Why specific technology choices were made
- How specific features work internally
- Database design justifications
- Error handling and edge cases
- Integration between components

These questions should require the student to think, not just recall.

For each question return:
{
  "question": "...",
  "difficulty": "medium",
  "category": "overview|technical|methodology|literature|results|ethics|scalability|curveball",
  "model_answer": "The ideal 3-5 sentence answer an examiner would want to hear",
  "section_reference": "Which thesis section this relates to"
}

Return ONLY a valid JSON array of 20 question objects. No markdown, no extra text."""

HARD_PROMPT = """You are a university examiner. Generate 15 HARD viva questions that test critical thinking and ability to defend decisions:
- Security vulnerabilities and how to address them
- Scalability challenges and solutions
- Comparison with alternative approaches
- Limitations and honest assessment
- What would you change with more time?
- Contradictions or gaps in the thesis
- Ethical implications
- Hypothetical scenarios ("What if 100K users...")

These should be the toughest questions an examiner could ask.

For each question return:
{
  "question": "...",
  "difficulty": "hard",
  "category": "overview|technical|methodology|literature|results|ethics|scalability|curveball",
  "model_answer": "The ideal 3-5 sentence answer an examiner would want to hear",
  "section_reference": "Which thesis section this relates to"
}

Return ONLY a valid JSON array of 15 question objects. No markdown, no extra text."""


def _parse_questions_response(response: str) -> list:
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    return json.loads(response.strip())


def generate_questions(thesis_analysis_json: str, preferred_provider: str = "auto") -> list:
    all_questions = []

    for prompt, label in [(EASY_PROMPT, "easy"), (MEDIUM_PROMPT, "medium"), (HARD_PROMPT, "hard")]:
        user_content = f"Thesis analysis:\n{thesis_analysis_json}"
        try:
            response = llm_service.call_llm(prompt, user_content, preferred=preferred_provider)
            questions = _parse_questions_response(response)
            all_questions.extend(questions)
            logger.info(f"Generated {len(questions)} {label} questions")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse {label} questions JSON, retrying...")
            try:
                response = llm_service.call_llm(
                    prompt + "\n\nCRITICAL: Return ONLY a valid JSON array. No markdown fences, no explanations.",
                    user_content,
                    preferred=preferred_provider,
                )
                questions = _parse_questions_response(response)
                all_questions.extend(questions)
                logger.info(f"Generated {len(questions)} {label} questions on retry")
            except Exception as e:
                logger.error(f"Failed to generate {label} questions after retry: {e}")
        except Exception as e:
            logger.error(f"Error generating {label} questions: {e}")

    return all_questions
