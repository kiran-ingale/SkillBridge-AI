from __future__ import annotations

import json
import os
from typing import Any

from litellm import completion

from app.core.config import get_settings
from skillbridge_agent.tools.diagnosis_tools import ROLE_MARKET_REQUIREMENTS

PASSING_SCORE = 75
INTERVIEW_DURATION_MINUTES = 16


def create_mock_interview(target_role: str, profile_summary: str = "", project_summary: str = "") -> dict[str, Any]:
    role_label = target_role.replace("_", " ")
    role_data = ROLE_MARKET_REQUIREMENTS.get(target_role, ROLE_MARKET_REQUIREMENTS["software_developer"])
    primary_skills = ", ".join(role_data["skills"][:4])
    return {
        "duration_minutes": INTERVIEW_DURATION_MINUTES,
        "passing_score": PASSING_SCORE,
        "questions": [
            {
                "id": "technical_1",
                "category": "technical",
                "question": f"For a {role_label} role, explain one project where you used {primary_skills}. What did you personally implement?",
            },
            {
                "id": "technical_2",
                "category": "technical",
                "question": "Describe a bug or failure you faced. How did you isolate the cause, fix it, and verify the fix?",
            },
            {
                "id": "technical_3",
                "category": "technical",
                "question": f"Solve a role-specific design problem: how would you build the core feature in this project? Mention data flow, edge cases, and testing.",
            },
            {
                "id": "technical_4",
                "category": "technical",
                "question": f"What are the most important edge cases for a beginner {role_label} project, and how would you test them?",
            },
            {
                "id": "technical_5",
                "category": "technical",
                "question": f"Explain one important concept from {primary_skills}. Give an example from your own work.",
            },
            {
                "id": "technical_6",
                "category": "technical",
                "question": "If your project works locally but fails after deployment, what exact debugging steps would you follow?",
            },
            {
                "id": "technical_7",
                "category": "technical",
                "question": "Describe how you would make your project more reliable, maintainable, and reviewable for a recruiter.",
            },
            {
                "id": "technical_8",
                "category": "technical",
                "question": "Give a simple DSA or problem-solving example related to this role. Mention approach, complexity, and trade-offs.",
            },
            {
                "id": "communication_1",
                "category": "communication",
                "question": "Give a 90-second interview answer for your strongest project: problem, your role, technical decisions, and result.",
            },
            {
                "id": "communication_2",
                "category": "communication",
                "question": "Why are you targeting this role, and what evidence proves you are ready for beginner-level work?",
            },
            {
                "id": "communication_3",
                "category": "communication",
                "question": "Explain one weakness in your current readiness and the concrete plan you are following to fix it.",
            },
            {
                "id": "communication_4",
                "category": "communication",
                "question": "Tell me about a time you received feedback on your work. What did you change after that feedback?",
            },
        ],
        "context": {
            "profile_summary": profile_summary,
            "project_summary": project_summary,
        },
    }


def evaluate_mock_interview(submission: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if settings.groq_api_key:
        os.environ["GROQ_API_KEY"] = settings.groq_api_key

    prompt = _evaluation_prompt(submission)
    try:
        response = completion(
            model=settings.skillbridge_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict fresher employability interview evaluator for engineering students in India. "
                        "Evaluate technical correctness, role readiness, communication clarity, evidence of project ownership, "
                        "and honesty. Penalize empty, generic, copied, or vague answers heavily."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
    except Exception:
        return _fallback_interview_evaluation(submission)

    technical_score = _bounded_int(data.get("technical_score"))
    communication_score = _bounded_int(data.get("communication_score"))
    score = _bounded_int(data.get("score"), round((technical_score * 0.6) + (communication_score * 0.4)))
    return {
        "score": score,
        "passed": score >= PASSING_SCORE,
        "technical_score": technical_score,
        "communication_score": communication_score,
        "feedback": _string_list(data.get("feedback"))[:6],
        "improvement_plan": _string_list(data.get("improvement_plan"))[:6],
    }


def _fallback_interview_evaluation(submission: dict[str, Any]) -> dict[str, Any]:
    answers = submission.get("answers", {})
    technical_keywords = [
        "api",
        "database",
        "sql",
        "auth",
        "test",
        "debug",
        "deploy",
        "validation",
        "edge",
        "security",
        "performance",
    ]
    communication_keywords = ["problem", "role", "built", "because", "result", "proof", "learned", "improved"]
    technical_answers = " ".join(
        answer for question_id, answer in answers.items() if question_id.startswith("technical")
    )
    communication_answers = " ".join(
        answer for question_id, answer in answers.items() if question_id.startswith("communication")
    )
    technical_score = _answer_score(technical_answers, technical_keywords)
    communication_score = _answer_score(communication_answers, communication_keywords)
    score = _bounded_int(round((technical_score * 0.6) + (communication_score * 0.4)))
    feedback = [
        "LiteLLM/Groq was unreachable, so SkillBridge used the local strict evaluator for this attempt.",
        "Technical answers need concrete implementation details, debugging evidence, tests, and trade-offs.",
        "Communication answers need a clear problem, your role, technical choices, and measurable result.",
    ]
    if score >= PASSING_SCORE:
        feedback = [
            "LiteLLM/Groq was unreachable, so SkillBridge used the local strict evaluator for this attempt.",
            "Your answers include enough technical and communication evidence to pass this mock interview.",
        ]
    return {
        "score": score,
        "passed": score >= PASSING_SCORE,
        "technical_score": technical_score,
        "communication_score": communication_score,
        "feedback": feedback,
        "improvement_plan": [
            "Add one deeper debugging story with root cause, fix, and verification.",
            "Practice a 90-second project explanation with problem, role, stack, and outcome.",
            "Tie every claimed skill to GitHub, README, test, deployment, or screenshot proof.",
        ],
    }


def _answer_score(answer: str, keywords: list[str]) -> int:
    text = answer.lower()
    words = text.split()
    if not words:
        return 0
    hits = sum(1 for keyword in keywords if keyword in text)
    if hits == 0:
        return min(15, len(words) // 5)
    return _bounded_int((hits * 8) + min(28, len(words) // 4))


def _evaluation_prompt(submission: dict[str, Any]) -> str:
    questions = submission.get("questions", [])
    answers = submission.get("answers", {})
    qa_lines = []
    for question in questions:
        question_id = question.get("id", "")
        qa_lines.append(
            "\n".join(
                [
                    f"Category: {question.get('category', '')}",
                    f"Question: {question.get('question', '')}",
                    f"Answer: {answers.get(question_id, '')}",
                ]
            )
        )

    return (
        "Evaluate this 16-minute mock interview. Return only JSON with keys: "
        "score, passed, technical_score, communication_score, feedback, improvement_plan.\n"
        "Scores must be realistic from 0 to 100. Empty answers should score 0-10. "
        "Very weak generic answers should score 10-25. Passing requires score >= 75.\n\n"
        f"Target role: {submission.get('target_role')}\n"
        f"Profile summary: {submission.get('profile_summary', '')}\n"
        f"Project summary: {submission.get('project_summary', '')}\n\n"
        + "\n\n---\n\n".join(qa_lines)
    )


def _bounded_int(value: Any, fallback: int = 0) -> int:
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        numeric = fallback
    return max(0, min(100, numeric))


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return ["Evaluation completed, but the model did not return detailed feedback."]
