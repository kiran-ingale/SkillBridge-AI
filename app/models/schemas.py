from typing import Literal

from pydantic import BaseModel, Field, field_validator


TargetRole = Literal[
    "software_developer",
    "frontend_developer",
    "backend_developer",
    "data_analyst",
    "qa_engineer",
    "embedded_iot_engineer",
    "cloud_devops_beginner",
]


class SkillRating(BaseModel):
    name: str
    rating: int = Field(ge=0, le=5)


class AssessmentInput(BaseModel):
    programming_score: int = Field(default=0, ge=0, le=100)
    dsa_score: int = Field(default=0, ge=0, le=100)
    communication_score: int = Field(default=0, ge=0, le=100)
    aptitude_score: int = Field(default=0, ge=0, le=100)
    notes: str = ""


class StudentProfileInput(BaseModel):
    name: str
    branch: str
    academic_year: str
    location: str = "India"
    target_role: TargetRole
    weekly_available_hours: int = Field(default=12, ge=1, le=80)
    requested_duration_days: int | None = Field(default=None, ge=1, le=365)
    resume_text: str = ""
    github_url: str | None = None
    linkedin_url: str | None = None
    project_description: str = ""
    self_rated_skills: list[SkillRating] = Field(default_factory=list)
    assessment: AssessmentInput = Field(default_factory=AssessmentInput)

    @field_validator("github_url", "linkedin_url", mode="before")
    @classmethod
    def normalize_optional_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        if not normalized.startswith(("http://", "https://")):
            normalized = f"https://{normalized}"
        return normalized


class DiagnosisResponse(BaseModel):
    diagnosis_id: str | None = None
    employability_score: int
    role_readiness_score: int
    recommended_duration_days: int
    requested_duration_days: int | None
    deadline_disclaimer: str | None
    top_gaps: list[str]
    strengths: list[str]
    market_signals: list[str]
    plan_phases: list[dict]
    first_project_assignment: dict
    mock_interview_questions: list[str]
    evidence_review: dict = Field(default_factory=dict)


class ResumeParseResponse(BaseModel):
    filename: str
    character_count: int
    text: str
    resume_report: dict


class ProgressTaskInput(BaseModel):
    diagnosis_id: str
    title: str
    status: Literal["todo", "in_progress", "done", "blocked"] = "todo"
    notes: str = ""


class ProgressTaskResponse(BaseModel):
    id: str
    diagnosis_id: str
    created_at: str
    title: str
    status: str
    notes: str


class DiagnosisRecord(BaseModel):
    id: str
    created_at: str
    student_name: str | None
    target_role: str | None
    employability_score: int | None
    role_readiness_score: int | None
    recommended_duration_days: int | None
    profile: dict
    result: dict


class AdaptationResponse(BaseModel):
    diagnosis_id: str
    adaptation: str
    recommended_change: str
    duration_adjustment_days: int
    next_actions: list[str]


class AssessmentSubmission(BaseModel):
    target_role: TargetRole
    coding_answer: str = ""
    dsa_answer: str = ""
    communication_answer: str = ""
    aptitude_answer: str = ""
    role_answers: dict[str, str] = Field(default_factory=dict)


class AssessmentEvaluationResponse(BaseModel):
    assessment: AssessmentInput
    skill_ratings: list[SkillRating]
    feedback: list[str]


class AuthRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class AuthResponse(BaseModel):
    token: str
    email: str


class TaskEvaluationRequest(BaseModel):
    task_title: str
    target_role: TargetRole


class TaskEvaluationSubmission(BaseModel):
    task_title: str
    target_role: TargetRole
    coding_answer: str = ""
    concept_answer: str = ""
    reflection_answer: str = ""
    mcq_answer: str = ""


class TaskEvaluationResult(BaseModel):
    score: int
    passed: bool
    feedback: list[str]
    resources: list[str]


class MockInterviewRequest(BaseModel):
    target_role: TargetRole
    profile_summary: str = ""
    project_summary: str = ""


class MockInterviewQuestion(BaseModel):
    id: str
    category: str
    question: str


class MockInterviewResponse(BaseModel):
    duration_minutes: int
    passing_score: int
    questions: list[MockInterviewQuestion]


class MockInterviewSubmission(BaseModel):
    target_role: TargetRole
    questions: list[MockInterviewQuestion]
    answers: dict[str, str]
    profile_summary: str = ""
    project_summary: str = ""


class MockInterviewResult(BaseModel):
    score: int
    passed: bool
    technical_score: int
    communication_score: int
    feedback: list[str]
    improvement_plan: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class CoachChatRequest(BaseModel):
    message: str
    context: dict = Field(default_factory=dict)
    history: list[ChatMessage] = Field(default_factory=list)


class CoachChatResponse(BaseModel):
    reply: str

