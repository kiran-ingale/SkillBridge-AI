# SkillBridge AI

Agentic employability coach for engineering students. It diagnoses job readiness from resume, GitHub, assessment answers, target role, and current market signals, then creates a personalized plan whose duration is estimated from the student's actual gaps.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Groq key:

```env
GROQ_API_KEY=your_groq_key_here
SKILLBRIDGE_MODEL=groq/llama-3.1-8b-instant
```

SkillBridge uses ADK's `LiteLlm` wrapper for Groq. Any Groq chat model supported by LiteLLM can be used with the `groq/` prefix, for example `groq/llama-3.1-8b-instant` or `groq/llama-3.3-70b-versatile`.

## Run the API

```powershell
uvicorn app.main:app --reload
```

Open:

- API health: `http://127.0.0.1:8000/health`
- Config status: `http://127.0.0.1:8000/config/status`
- Docs: `http://127.0.0.1:8000/docs`

Useful MVP endpoints:

- `POST /resume/parse` with a PDF file field named `file`
- `POST /diagnose` with profile, target role, assessment, resume text, and GitHub URL
- `GET /diagnoses` and `GET /diagnoses/{diagnosis_id}` for saved diagnosis state
- `POST /progress/tasks` and `GET /progress/{diagnosis_id}` for progress tracking
- `POST /adapt/{diagnosis_id}` for weekly plan adaptation

## Run the ADK agent

The scaffold was created with:

```powershell
adk create skillbridge_agent
```

After adding `GROQ_API_KEY`, run:

```powershell
adk web
```

Then select `skillbridge_agent`.

## MVP Pipeline

1. Student profile intake
2. Resume analysis
3. GitHub/project analysis
4. Role-market requirement synthesis through the SkillBridge market rubric
5. Employability diagnosis
6. Role-fit and gap analysis
7. Personalized duration estimation
8. Plan generation with deadline disclaimer when needed
9. Project mentoring and weekly adaptation

The FastAPI endpoint currently uses deterministic offline market rubrics so it can run without an LLM call. The ADK agent is wired through Groq via LiteLLM after `GROQ_API_KEY` is configured.

GitHub analysis inspects public repositories when a GitHub URL is supplied. Add `GITHUB_TOKEN` to avoid low anonymous API rate limits.
