import fitz  # PyMuPDF
from docx import Document
import re
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def extract_text_from_pdf(file_path: str) -> dict:
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()

    if not pages:
        raise ValueError("Could not extract text. Please upload a digital PDF, not a scanned image.")

    full_text = "\n\n".join(pages)
    full_text = _clean_text(full_text)
    word_count = len(full_text.split())

    return {
        "text": full_text,
        "page_count": len(pages),
        "word_count": word_count,
    }


def extract_text_from_docx(file_path: str) -> dict:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    full_text = _clean_text(full_text)
    word_count = len(full_text.split())

    return {
        "text": full_text,
        "page_count": 0,
        "word_count": word_count,
    }


def _clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def extract_text(file_path: str, file_type: str) -> dict:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
