import json
import logging
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

THESIS_ANALYSIS_PROMPT = """You are an academic thesis analyst. Read the following thesis/FYP report and extract key information.

Return ONLY valid JSON with no additional text:
{
  "project_title": "...",
  "abstract_summary": "2-3 sentence summary",
  "technologies": ["Next.js", "FastAPI", "SQLite"],
  "methodology": "qualitative|quantitative|mixed|experimental|design-based",
  "research_questions": ["RQ1...", "RQ2..."],
  "key_findings": ["Finding 1...", "Finding 2..."],
  "limitations": ["Limitation 1...", "Limitation 2..."],
  "future_work": ["Future 1...", "Future 2..."],
  "sections": [
    {"name": "Introduction", "detected": true},
    {"name": "Literature Review", "detected": true},
    {"name": "Methodology", "detected": true},
    {"name": "Implementation", "detected": true},
    {"name": "Results", "detected": true},
    {"name": "Conclusion", "detected": true}
  ]
}"""


def analyze_thesis(extracted_text: str, preferred_provider: str = "auto") -> dict:
    text_to_analyze = extracted_text
    words = extracted_text.split()
    if len(words) > 5000:
        text_to_analyze = " ".join(words[:5000])
        logger.info(f"Thesis text truncated from {len(words)} to 5000 words for analysis")

    user_content = f"Thesis text:\n{text_to_analyze}"

    response = llm_service.call_llm(THESIS_ANALYSIS_PROMPT, user_content, preferred=preferred_provider)

    try:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        analysis = json.loads(response.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse thesis analysis JSON. Response: {response[:200]}")
        response_retry = llm_service.call_llm(
            THESIS_ANALYSIS_PROMPT + "\n\nIMPORTANT: Return ONLY valid JSON, no markdown, no extra text.",
            user_content,
            preferred=preferred_provider,
        )
        try:
            response_retry = response_retry.strip()
            if response_retry.startswith("```json"):
                response_retry = response_retry[7:]
            if response_retry.startswith("```"):
                response_retry = response_retry[3:]
            if response_retry.endswith("```"):
                response_retry = response_retry[:-3]
            analysis = json.loads(response_retry.strip())
        except json.JSONDecodeError:
            raise ValueError("AI returned invalid JSON for thesis analysis after retry. Please try again.")

    return analysis
