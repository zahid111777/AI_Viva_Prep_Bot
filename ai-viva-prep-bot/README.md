# AI Viva Prep Bot

AI-Powered Viva/Defense Preparation Bot that reads your thesis, generates custom viva questions, conducts interactive mock viva sessions, scores answers with feedback, and produces readiness reports.

## Quick Start

### Backend

```bash
cd ai-viva-prep-bot/backend

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Configure .env with at least one API key (Groq, OpenRouter, OpenAI, or Gemini)

# Run server
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd ai-viva-prep-bot/frontend
npm run dev
```

App: http://localhost:3000

## Features

- **Multi-LLM Support**: Groq, OpenRouter, OpenAI, Gemini with automatic fallback
- **Thesis Analysis**: Upload PDF/DOCX, AI detects project title, technologies, methodology
- **50+ Custom Questions**: Easy, Medium, Hard across 8 categories
- **Mock Viva Sessions**: Full mock, topic practice, quick fire modes
- **AI Scoring**: 0-10 scoring with detailed feedback, strengths, weaknesses
- **Follow-up Questions**: AI probes deeper based on your answers
- **Readiness Reports**: Overall score, strong/weak areas, study recommendations
- **PDF Export**: Study guide and Q&A PDF downloads
- **Admin Panel**: Platform analytics and user management

## Tech Stack

- **Frontend**: Next.js 14 (App Router), Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: SQLite via SQLAlchemy
- **Auth**: JWT tokens
- **AI**: Multi-provider LLM (Groq, OpenRouter, OpenAI, Gemini)
