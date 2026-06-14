from __future__ import annotations

import json
import os
from typing import Any

from litellm import completion

from app.core.config import get_settings


def answer_student_chat(message: str, context: dict[str, Any], history: list[dict[str, str]]) -> dict[str, str]:
    settings = get_settings()
    if settings.groq_api_key:
        os.environ["GROQ_API_KEY"] = settings.groq_api_key

    compact_context = _compact_context(context)
    messages = [
        {
            "role": "system",
            "content": (
                "You are SkillBridge AI's personalized employability coach for engineering students in India. "
                "Use the provided student context: target role, diagnosis gaps, skill test scores, plan, progress, "
                "project mentor state, and mock interview state. Give specific, actionable next steps. "
                "Do not give generic roadmaps. If the student is blocked, reduce scope and assign the next small task."
            ),
        },
        {
            "role": "user",
            "content": "Student context JSON:\n" + json.dumps(compact_context, ensure_ascii=True)[:6000],
        },
    ]
    for item in history[-6:]:
        if item.get("role") in {"user", "assistant"} and item.get("content"):
            messages.append({"role": item["role"], "content": item["content"][:1200]})
    messages.append({"role": "user", "content": message[:1600]})

    try:
        response = completion(
            model=settings.skillbridge_model,
            messages=messages,
            temperature=0.35,
        )
        reply = response.choices[0].message.content or ""
        if reply.strip():
            return {"reply": reply.strip()}
    except Exception:
        pass

    return {"reply": _fallback_reply(message, compact_context)}


def _compact_context(context: dict[str, Any]) -> dict[str, Any]:
    profile = context.get("profile") or {}
    diagnosis = context.get("overallReport") or context.get("profileDiagnosis") or {}
    evaluation = context.get("latestEvaluation") or {}
    execution = context.get("execution") or {}
    tasks = execution.get("tasks") or []
    return {
        "student": {
            "name": profile.get("name"),
            "branch": profile.get("branch"),
            "academic_year": profile.get("academic_year"),
            "target_role": profile.get("target_role"),
            "weekly_available_hours": profile.get("weekly_available_hours"),
            "requested_duration_days": profile.get("requested_duration_days"),
            "github_url_present": bool(profile.get("github_url")),
            "linkedin_url_present": bool(profile.get("linkedin_url")),
        },
        "scores": {
            "employability": diagnosis.get("employability_score"),
            "role_readiness": diagnosis.get("role_readiness_score"),
            "recommended_duration_days": diagnosis.get("recommended_duration_days"),
            "assessment": evaluation.get("assessment"),
        },
        "gaps": diagnosis.get("top_gaps", []),
        "test_feedback": evaluation.get("feedback", []),
        "plan_phases": diagnosis.get("plan_phases", [])[:4],
        "current_execution": {
            "phase": (execution.get("phase") or {}).get("phase"),
            "completed_tasks": [task.get("title") for task in tasks if task.get("completed")],
            "active_tasks": [task.get("title") for task in tasks if not task.get("completed") and not task.get("locked")],
            "locked_count": sum(1 for task in tasks if task.get("locked")),
            "last_scores": [
                {"task": task.get("title"), "score": task.get("lastScore")}
                for task in tasks
                if task.get("lastScore") is not None
            ],
        },
        "first_project": diagnosis.get("first_project_assignment"),
        "evidence_review": diagnosis.get("evidence_review"),
    }


def _fallback_reply(message: str, context: dict[str, Any]) -> str:
    student = context.get("student", {})
    scores = context.get("scores", {})
    gaps = context.get("gaps") or []
    execution = context.get("current_execution", {})
    active_tasks = execution.get("active_tasks") or []
    target_role = str(student.get("target_role") or "your target role").replace("_", " ")
    name = student.get("name") or "there"

    next_task = active_tasks[0] if active_tasks else None
    weakest_gap = gaps[0] if gaps else "No diagnosis gap is available yet. Complete the profile diagnosis and skill test first."
    reply = [
        f"Hi {name}, based on your current SkillBridge context for {target_role}, your role readiness is {scores.get('role_readiness', 'not available')}/100.",
        f"Your highest-priority gap right now: {weakest_gap}",
    ]
    if next_task:
        reply.append(f"Work on this next task before jumping ahead: {next_task}")
        reply.append("After completing it, take the task evaluation and only move forward if you score 75+.")
    else:
        reply.append("Next best move: complete the skill test, generate the overall plan, then execute the first unlocked task.")

    if "project" in message.lower():
        project = context.get("first_project") or {}
        reply.append(f"For your project, keep the scope tight: {project.get('title', 'build one role-specific proof project')}. Add README, tests or screenshots, and a clear resume bullet.")
    return "\n\n".join(reply)
