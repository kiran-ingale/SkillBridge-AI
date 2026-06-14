from app.models.schemas import StudentProfileInput
from app.services.storage import save_diagnosis
from skillbridge_agent.tools.diagnosis_tools import (
    analyze_github_profile,
    analyze_linkedin_profile,
    analyze_resume_text,
    estimate_plan_duration,
    generate_personalized_plan,
    get_market_requirements,
    score_employability,
)


def run_diagnosis(profile: StudentProfileInput) -> dict:
    """Run the deterministic MVP pipeline used by the API.

    The ADK agent uses the same functions as tools, so the product has one
    shared scoring surface whether it is called by FastAPI or by the agent.
    """
    profile_payload = profile.model_dump(mode="json")
    resume_report = analyze_resume_text(profile.resume_text)
    github_report = analyze_github_profile(
        github_url=str(profile.github_url) if profile.github_url else "",
        project_description=profile.project_description,
    )
    linkedin_report = analyze_linkedin_profile(str(profile.linkedin_url) if profile.linkedin_url else "")
    market_report = get_market_requirements(profile.target_role, profile.location)
    score_report = score_employability(
        profile=profile_payload,
        resume_report=resume_report,
        github_report=github_report,
        linkedin_report=linkedin_report,
        market_report=market_report,
    )
    duration_report = estimate_plan_duration(
        profile=profile_payload,
        score_report=score_report,
        market_report=market_report,
    )
    plan_report = generate_personalized_plan(
        profile=profile_payload,
        score_report=score_report,
        duration_report=duration_report,
        market_report=market_report,
    )

    result = {
        **score_report,
        **duration_report,
        **plan_report,
        "market_signals": market_report["market_signals"],
    }
    diagnosis_id = save_diagnosis(profile_payload, result)
    return {"diagnosis_id": diagnosis_id, **result}
