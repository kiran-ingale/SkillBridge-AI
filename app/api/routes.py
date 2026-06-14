from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    AdaptationResponse,
    AssessmentEvaluationResponse,
    AssessmentSubmission,
    AuthRequest,
    AuthResponse,
    CoachChatRequest,
    CoachChatResponse,
    DiagnosisRecord,
    DiagnosisResponse,
    MockInterviewRequest,
    MockInterviewResponse,
    MockInterviewResult,
    MockInterviewSubmission,
    ProgressTaskInput,
    ProgressTaskResponse,
    ResumeParseResponse,
    StudentProfileInput,
    TaskEvaluationRequest,
    TaskEvaluationResult,
    TaskEvaluationSubmission,
)
from app.services.assessment import (
    evaluate_assessment,
    evaluate_task_submission,
    get_assessment_for_role,
    get_task_evaluation,
)
from app.core.config import get_settings
from app.services.auth import authenticate_user, create_user
from app.services.coach_chat import answer_student_chat
from app.services.diagnosis import run_diagnosis
from app.services.mock_interview import create_mock_interview, evaluate_mock_interview
from app.services.resume_parser import extract_resume_text_from_pdf
from app.services.storage import get_diagnosis, list_diagnoses, list_progress_tasks, save_progress_task
from skillbridge_agent.tools.diagnosis_tools import analyze_resume_text
from skillbridge_agent.tools.diagnosis_tools import adapt_plan_from_progress

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "skillbridge-ai"}


@router.get("/config/status")
def config_status() -> dict:
    settings = get_settings()
    model = settings.skillbridge_model
    return {
        "model": model,
        "provider": "groq" if model.startswith("groq/") else "google",
        "groq_api_key_present": bool(settings.groq_api_key),
        "google_api_key_present": bool(settings.google_api_key),
        "github_token_present": bool(settings.github_token),
        "search_api_key_present": bool(settings.search_api_key),
    }


@router.post("/auth/signup", response_model=AuthResponse)
def signup(request: AuthRequest) -> dict[str, str]:
    try:
        return create_user(request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login", response_model=AuthResponse)
def login(request: AuthRequest) -> dict[str, str]:
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return user


@router.get("/assessment/{target_role}")
def assessment(target_role: str) -> dict:
    return get_assessment_for_role(target_role)


@router.post("/assessment/evaluate", response_model=AssessmentEvaluationResponse)
def evaluate(submission: AssessmentSubmission) -> dict:
    return evaluate_assessment(submission.model_dump())


@router.post("/task-evaluation")
def task_evaluation(request: TaskEvaluationRequest) -> dict:
    return get_task_evaluation(request.task_title, request.target_role)


@router.post("/task-evaluation/evaluate", response_model=TaskEvaluationResult)
def evaluate_task(submission: TaskEvaluationSubmission) -> dict:
    return evaluate_task_submission(submission.model_dump())


@router.post("/mock-interview", response_model=MockInterviewResponse)
def mock_interview(request: MockInterviewRequest) -> dict:
    return create_mock_interview(
        request.target_role,
        profile_summary=request.profile_summary,
        project_summary=request.project_summary,
    )


@router.post("/mock-interview/evaluate", response_model=MockInterviewResult)
def evaluate_interview(submission: MockInterviewSubmission) -> dict:
    try:
        return evaluate_mock_interview(submission.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI interview evaluation failed: {exc}") from exc


@router.post("/chat", response_model=CoachChatResponse)
def coach_chat(request: CoachChatRequest) -> dict[str, str]:
    return answer_student_chat(
        message=request.message,
        context=request.context,
        history=[item.model_dump() for item in request.history],
    )


@router.post("/diagnose", response_model=DiagnosisResponse)
def diagnose(profile: StudentProfileInput) -> dict:
    return run_diagnosis(profile)


@router.get("/diagnoses", response_model=list[DiagnosisRecord])
def diagnoses() -> list[dict]:
    return list_diagnoses()


@router.get("/diagnoses/{diagnosis_id}", response_model=DiagnosisRecord)
def diagnosis(diagnosis_id: str) -> dict:
    record = get_diagnosis(diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Diagnosis not found.")
    return record


@router.post("/progress/tasks", response_model=ProgressTaskResponse)
def create_progress_task(task: ProgressTaskInput) -> dict:
    if not get_diagnosis(task.diagnosis_id):
        raise HTTPException(status_code=404, detail="Diagnosis not found.")
    return save_progress_task(
        diagnosis_id=task.diagnosis_id,
        title=task.title,
        status=task.status,
        notes=task.notes,
    )


@router.get("/progress/{diagnosis_id}", response_model=list[ProgressTaskResponse])
def progress(diagnosis_id: str) -> list[dict]:
    if not get_diagnosis(diagnosis_id):
        raise HTTPException(status_code=404, detail="Diagnosis not found.")
    return list_progress_tasks(diagnosis_id)


@router.post("/adapt/{diagnosis_id}", response_model=AdaptationResponse)
def adapt(diagnosis_id: str) -> dict:
    record = get_diagnosis(diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Diagnosis not found.")
    adaptation = adapt_plan_from_progress(
        diagnosis_result=record["result"],
        progress_tasks=list_progress_tasks(diagnosis_id),
    )
    return {"diagnosis_id": diagnosis_id, **adaptation}


@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported for now.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume is empty.")

    try:
        text = extract_resume_text_from_pdf(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not parse the PDF resume.") from exc

    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in the PDF resume.")

    return {
        "filename": filename,
        "character_count": len(text),
        "text": text,
        "resume_report": analyze_resume_text(text),
    }
