from __future__ import annotations

import math
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()
load_dotenv("skillbridge_agent/.env")


ROLE_MARKET_REQUIREMENTS = {
    "backend_developer": {
        "base_hours": 90,
        "skills": ["REST APIs", "SQL", "authentication", "deployment", "testing", "Git"],
        "project": "Build and deploy a job application tracker API with auth, PostgreSQL, tests, and OpenAPI docs.",
        "signals": [
            "Entry-level backend roles commonly expect one deployed API project.",
            "SQL, authentication, and debugging evidence matter more than certificates.",
            "README quality and API documentation are useful proof-of-work signals.",
        ],
    },
    "frontend_developer": {
        "base_hours": 75,
        "skills": ["HTML/CSS", "JavaScript", "React", "responsive UI", "API integration", "deployment"],
        "project": "Build a responsive internship tracker dashboard using React, API integration, filters, and deployment.",
        "signals": [
            "Frontend roles expect polished responsive interfaces and component discipline.",
            "API integration and deployment separate resume projects from classroom demos.",
            "Accessibility and state management are strong differentiators for beginners.",
        ],
    },
    "data_analyst": {
        "base_hours": 80,
        "skills": ["SQL", "Excel", "Python", "statistics", "dashboarding", "business communication"],
        "project": "Analyze an employability dataset and publish a dashboard with SQL findings and business recommendations.",
        "signals": [
            "Analyst roles expect SQL, spreadsheets, visualization, and clear business interpretation.",
            "A portfolio case study is stronger than isolated notebook screenshots.",
            "Communication quality affects analyst readiness heavily.",
        ],
    },
    "qa_engineer": {
        "base_hours": 65,
        "skills": ["manual testing", "test cases", "bug reports", "automation basics", "API testing", "SDLC"],
        "project": "Create a QA portfolio with test cases, API tests, bug reports, and one automation suite.",
        "signals": [
            "QA fresher roles value structured thinking and clean bug reports.",
            "Postman/API testing plus basic automation improves internship readiness.",
        ],
    },
    "software_developer": {
        "base_hours": 95,
        "skills": ["programming fundamentals", "DSA", "Git", "projects", "debugging", "communication"],
        "project": "Build a full-stack student productivity app with auth, CRUD, deployment, and tests.",
        "signals": [
            "General software roles need fundamentals plus at least one complete project.",
            "Debugging and explanation ability are key interview filters.",
        ],
    },
    "embedded_iot_engineer": {
        "base_hours": 110,
        "skills": ["C/C++", "microcontrollers", "sensors", "serial communication", "debugging", "documentation"],
        "project": "Build an IoT attendance or environment monitor with sensor readings, dashboard, and documentation.",
        "signals": [
            "Embedded/IoT roles expect hardware proof, debugging logs, and clear circuit documentation.",
            "A demo video can compensate when recruiters cannot run the hardware project.",
        ],
    },
    "cloud_devops_beginner": {
        "base_hours": 120,
        "skills": ["Linux", "networking basics", "Docker", "CI/CD", "cloud deployment", "monitoring"],
        "project": "Containerize and deploy a web app with CI/CD, logs, health checks, and cloud documentation.",
        "signals": [
            "Beginner DevOps roles expect Linux, Docker, deployment, and troubleshooting evidence.",
            "Screenshots, architecture diagrams, and runbooks help prove practical ability.",
        ],
    },
}


def _count_matches(text: str, keywords: list[str]) -> int:
    normalized = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in normalized)


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def analyze_resume_text(resume_text: str) -> dict[str, Any]:
    """Analyze pasted resume text for employability proof signals."""
    text = resume_text or ""
    action_words = ["built", "created", "developed", "deployed", "improved", "automated", "analyzed"]
    proof_words = ["github", "demo", "deployed", "users", "accuracy", "api", "dashboard", "tests"]
    weak_words = ["hardworking", "quick learner", "team player", "passionate"]

    word_count = len(re.findall(r"\w+", text))
    action_score = min(25, _count_matches(text, action_words) * 5)
    proof_score = min(35, _count_matches(text, proof_words) * 5)
    structure_score = 20 if all(section in text.lower() for section in ["project", "skill"]) else 8
    length_score = 20 if 120 <= word_count <= 800 else 10
    penalty = min(15, _count_matches(text, weak_words) * 4)

    score = _clamp(action_score + proof_score + structure_score + length_score - penalty)
    gaps = []
    if proof_score < 15:
        gaps.append("Resume lacks proof-of-work signals such as deployed links, GitHub, tests, or measurable outcomes.")
    if action_score < 10:
        gaps.append("Resume bullets need stronger action verbs and ownership.")
    if structure_score < 15:
        gaps.append("Resume should clearly separate skills, projects, education, and experience.")

    return {
        "resume_score": score,
        "word_count": word_count,
        "gaps": gaps,
        "strengths": ["Resume includes project/skill evidence."] if score >= 60 else [],
    }


def _parse_github_url(github_url: str) -> tuple[str | None, str | None]:
    match = re.search(r"github\.com/([^/\s?#]+)(?:/([^/\s?#]+))?", github_url)
    if not match:
        return None, None
    owner = match.group(1)
    repo = match.group(2)
    if repo and repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_github_evidence(github_url: str) -> dict[str, Any]:
    owner, repo = _parse_github_url(github_url)
    if not owner:
        return {"source": "invalid_url", "repos": [], "error": "Could not parse GitHub owner from URL."}

    headers = _github_headers()
    timeout = httpx.Timeout(6.0)
    repos: list[dict[str, Any]] = []

    try:
        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            if repo:
                response = client.get(f"https://api.github.com/repos/{owner}/{repo}")
                response.raise_for_status()
                repo_payloads = [response.json()]
            else:
                response = client.get(
                    f"https://api.github.com/users/{owner}/repos",
                    params={"sort": "updated", "per_page": 8},
                )
                response.raise_for_status()
                repo_payloads = response.json()

            for payload in repo_payloads[:8]:
                full_name = payload.get("full_name", "")
                repo_text = " ".join(
                    str(value or "")
                    for value in [
                        payload.get("name"),
                        payload.get("description"),
                        payload.get("language"),
                        payload.get("homepage"),
                        " ".join(payload.get("topics") or []),
                    ]
                )
                has_readme = False
                has_tests = False
                if full_name:
                    readme_response = client.get(f"https://api.github.com/repos/{full_name}/readme")
                    has_readme = readme_response.status_code == 200

                    contents_response = client.get(f"https://api.github.com/repos/{full_name}/contents")
                    if contents_response.status_code == 200:
                        contents = contents_response.json()
                        if isinstance(contents, list):
                            names = " ".join(item.get("name", "") for item in contents).lower()
                            has_tests = any(token in names for token in ["test", "spec", "pytest", "jest"])

                repos.append(
                    {
                        "name": payload.get("name"),
                        "full_name": full_name,
                        "description": payload.get("description"),
                        "language": payload.get("language"),
                        "stars": payload.get("stargazers_count", 0),
                        "updated_at": payload.get("pushed_at"),
                        "homepage": payload.get("homepage"),
                        "has_readme": has_readme,
                        "has_tests": has_tests,
                        "text": repo_text,
                    }
                )
    except Exception as exc:
        return {"source": "github_api_error", "repos": [], "error": str(exc)}

    return {"source": "github_api", "repos": repos, "error": None}


def analyze_github_profile(github_url: str = "", project_description: str = "") -> dict[str, Any]:
    """Score GitHub/project evidence from URL, public repo metadata, and project text."""
    combined = f"{github_url} {project_description}".lower()
    github_evidence = _fetch_github_evidence(github_url) if github_url else {"source": "not_provided", "repos": []}
    repo_text = " ".join(repo.get("text", "") for repo in github_evidence.get("repos", [])).lower()
    combined_with_repos = f"{combined} {repo_text}"
    repos = github_evidence.get("repos", [])

    signals = {
        "has_github": bool(github_url),
        "has_public_repos": bool(repos),
        "has_readme": "readme" in combined or any(repo.get("has_readme") for repo in repos),
        "has_deployment": any(
            word in combined_with_repos for word in ["deploy", "vercel", "render", "railway", "netlify", "cloud"]
        )
        or any(repo.get("homepage") for repo in repos),
        "has_tests": any(word in combined_with_repos for word in ["test", "pytest", "jest", "unit"])
        or any(repo.get("has_tests") for repo in repos),
        "has_database": any(word in combined_with_repos for word in ["sql", "postgres", "mysql", "mongodb", "database"]),
        "has_api": any(word in combined_with_repos for word in ["api", "fastapi", "express", "rest"]),
        "has_recent_activity": bool(repos),
    }
    score = 10 if signals["has_github"] else 0
    score += sum(15 for key, present in signals.items() if key != "has_github" and present)
    score = _clamp(score)

    gaps = []
    if not signals["has_github"]:
        gaps.append("No GitHub URL was provided, so project proof is weak.")
    elif not signals["has_public_repos"]:
        gaps.append("GitHub URL was provided, but public repositories could not be inspected.")
    if not signals["has_deployment"]:
        gaps.append("Project evidence does not show deployment.")
    if not signals["has_tests"]:
        gaps.append("Project evidence does not show tests.")
    if not signals["has_readme"]:
        gaps.append("Project evidence does not mention a clear README.")

    return {
        "github_score": score,
        "signals": signals,
        "gaps": gaps,
        "source": github_evidence.get("source"),
        "github_error": github_evidence.get("error"),
        "repos_reviewed": [
            {
                "name": repo.get("name"),
                "language": repo.get("language"),
                "has_readme": repo.get("has_readme"),
                "has_tests": repo.get("has_tests"),
                "homepage": repo.get("homepage"),
            }
            for repo in repos[:5]
        ],
    }


def analyze_linkedin_profile(linkedin_url: str = "") -> dict[str, Any]:
    """Score LinkedIn profile evidence from the public URL structure.

    LinkedIn blocks most unauthenticated scraping, so this MVP uses the URL as
    explicit professional-profile evidence and reports that limitation clearly.
    """
    url = (linkedin_url or "").strip()
    match = re.search(r"linkedin\.com/in/([^/\s?#]+)", url)
    handle = match.group(1) if match else None
    signals = {
        "has_linkedin": bool(url),
        "valid_profile_url": bool(handle),
        "custom_profile_slug": bool(handle and len(handle) >= 5 and not handle.isdigit()),
    }
    score = 0
    if signals["has_linkedin"]:
        score += 20
    if signals["valid_profile_url"]:
        score += 25
    if signals["custom_profile_slug"]:
        score += 15
    score = _clamp(score)

    gaps = []
    if not signals["has_linkedin"]:
        gaps.append("No LinkedIn URL was provided, so professional profile evidence is missing.")
    elif not signals["valid_profile_url"]:
        gaps.append("LinkedIn URL does not look like a public /in/ profile link.")

    strengths = []
    if signals["valid_profile_url"]:
        strengths.append("LinkedIn profile URL is present and can be used as professional identity proof.")

    return {
        "linkedin_score": score,
        "handle": handle,
        "signals": signals,
        "gaps": gaps,
        "strengths": strengths,
        "source": "linkedin_url" if url else "not_provided",
        "inspection_note": (
            "LinkedIn content is not scraped in this MVP because public profile pages usually require login "
            "or block automated reads. The URL is still used as profile evidence."
        ),
    }


def get_market_requirements(target_role: str, location: str = "India") -> dict[str, Any]:
    """Return role expectations used by the planner.

    This is the offline MVP fallback. In production, the Web Research Agent
    should augment this with search results and citations for current openings.
    """
    role_data = ROLE_MARKET_REQUIREMENTS.get(target_role, ROLE_MARKET_REQUIREMENTS["software_developer"])
    return {
        "target_role": target_role,
        "location": location,
        "required_skills": role_data["skills"],
        "base_hours": role_data["base_hours"],
        "market_signals": role_data["signals"],
        "recommended_project": role_data["project"],
    }


def score_employability(
    profile: dict[str, Any],
    resume_report: dict[str, Any],
    github_report: dict[str, Any],
    market_report: dict[str, Any],
    linkedin_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    linkedin_report = linkedin_report or {"linkedin_score": 0, "gaps": [], "strengths": []}
    assessment = profile.get("assessment", {})
    skills = {item["name"].lower(): item["rating"] for item in profile.get("self_rated_skills", [])}
    target_role = profile.get("target_role") or market_report.get("target_role") or "software_developer"
    fallback_market = get_market_requirements(target_role, profile.get("location", "India"))
    required_skills = market_report.get("required_skills") or fallback_market["required_skills"]
    role_skill_hits = sum(1 for skill in required_skills if skill.lower() in skills and skills[skill.lower()] >= 3)
    role_skill_score = (role_skill_hits / max(len(required_skills), 1)) * 100

    programming = assessment.get("programming_score", 0)
    dsa = assessment.get("dsa_score", 0)
    communication = assessment.get("communication_score", 0)
    aptitude = assessment.get("aptitude_score", 0)

    employability = (
        programming * 0.15
        + dsa * 0.12
        + communication * 0.10
        + aptitude * 0.08
        + resume_report["resume_score"] * 0.16
        + github_report["github_score"] * 0.19
        + linkedin_report["linkedin_score"] * 0.05
        + role_skill_score * 0.15
    )
    role_readiness = (
        programming * 0.15
        + dsa * 0.10
        + github_report["github_score"] * 0.26
        + linkedin_report["linkedin_score"] * 0.04
        + role_skill_score * 0.30
        + communication * 0.15
    )

    gaps = [*resume_report["gaps"], *github_report["gaps"], *linkedin_report["gaps"]]
    if programming < 55:
        gaps.append("Programming fundamentals need strengthening before serious applications.")
    if dsa < 45:
        gaps.append("DSA/problem-solving score is below typical fresher interview expectations.")
    if communication < 55:
        gaps.append("Communication and explanation quality need mock interview practice.")
    missing_role_skills = [
        skill for skill in required_skills if skills.get(skill.lower(), 0) < 3
    ]
    if missing_role_skills:
        gaps.append("Missing or weak role-specific skills: " + ", ".join(missing_role_skills) + ".")

    strengths = []
    if resume_report["resume_score"] >= 65:
        strengths.append("Resume has some usable structure and proof signals.")
    if github_report["github_score"] >= 55:
        strengths.append("Project/GitHub evidence is usable with polishing.")
    if linkedin_report["linkedin_score"] >= 45:
        strengths.append("LinkedIn URL is present as professional profile proof.")
    if programming >= 65:
        strengths.append("Programming fundamentals appear above beginner level.")

    return {
        "employability_score": _clamp(employability),
        "role_readiness_score": _clamp(role_readiness),
        "top_gaps": gaps[:7],
        "strengths": strengths or ["Student has enough input data to begin a structured improvement plan."],
        "evidence_review": {
            "github": {
                "score": github_report["github_score"],
                "source": github_report.get("source"),
                "repos_reviewed": github_report.get("repos_reviewed", []),
                "signals": github_report.get("signals", {}),
                "gaps": github_report.get("gaps", []),
            },
            "linkedin": {
                "score": linkedin_report["linkedin_score"],
                "source": linkedin_report.get("source"),
                "handle": linkedin_report.get("handle"),
                "signals": linkedin_report.get("signals", {}),
                "gaps": linkedin_report.get("gaps", []),
                "inspection_note": linkedin_report.get("inspection_note"),
            },
        },
    }


def estimate_plan_duration(
    profile: dict[str, Any],
    score_report: dict[str, Any],
    market_report: dict[str, Any],
) -> dict[str, Any]:
    target_role = profile.get("target_role") or market_report.get("target_role") or "software_developer"
    fallback_market = get_market_requirements(target_role, profile.get("location", "India"))
    base_hours = market_report.get("base_hours") or fallback_market["base_hours"]
    employability_gap = 100 - score_report.get("employability_score", 50)
    role_gap = 100 - score_report.get("role_readiness_score", 50)
    gap_hours = (employability_gap * 0.8) + (role_gap * 1.1) + (len(score_report.get("top_gaps", [])) * 4)
    total_hours = base_hours + gap_hours

    weekly_hours = max(1, int(profile.get("weekly_available_hours", 12)))
    recommended_days = max(7, math.ceil((total_hours / weekly_hours) * 7))
    requested_days = profile.get("requested_duration_days")

    disclaimer = None
    if requested_days and requested_days < recommended_days:
        disclaimer = (
            f"Requested duration is {requested_days} days, but the evidence-based estimate is "
            f"{recommended_days} days. A compressed plan can prioritize minimum viable readiness, "
            "but some depth in projects, interviews, or role-specific skills may remain weaker."
        )

    return {
        "recommended_duration_days": recommended_days,
        "requested_duration_days": requested_days,
        "estimated_total_hours": round(total_hours),
        "deadline_disclaimer": disclaimer,
    }


def generate_personalized_plan(
    profile: dict[str, Any],
    score_report: dict[str, Any],
    duration_report: dict[str, Any],
    market_report: dict[str, Any],
) -> dict[str, Any]:
    target_role = profile.get("target_role") or market_report.get("target_role") or "software_developer"
    fallback_market = get_market_requirements(target_role, profile.get("location", "India"))
    total_days = duration_report.get("recommended_duration_days", 30)
    profile_days = max(2, round(total_days * 0.12))
    project_days = max(7, round(total_days * 0.45))
    fundamentals_days = max(5, round(total_days * 0.23))
    interview_days = max(4, total_days - profile_days - project_days - fundamentals_days)

    project = {
        "title": market_report.get("recommended_project") or fallback_market["recommended_project"],
        "acceptance_criteria": [
            "Public GitHub repository with clear README and setup steps.",
            "At least one deployed/demo link or screen-recorded walkthrough.",
            "Evidence of debugging, tests, or validation.",
            "Resume bullet rewritten with measurable technical impact.",
        ],
    }

    phases = [
        {
            "phase": "Profile and evidence repair",
            "duration_days": profile_days,
            "tasks": [
                "Rewrite resume bullets around projects, impact, tools, and outcomes.",
                "Clean GitHub profile and add README files to important repositories.",
                "Map target role requirements to visible proof in resume and GitHub.",
            ],
        },
        {
            "phase": "Role-specific proof project",
            "duration_days": project_days,
            "tasks": [
                project["title"],
                "Break the project into milestones and push progress daily.",
                "Add deployment, documentation, and validation so it becomes resume-worthy.",
            ],
        },
        {
            "phase": "Fundamentals and weak-area repair",
            "duration_days": fundamentals_days,
            "tasks": [
                "Practice the weakest programming and DSA topics found in assessment.",
                "Explain solved problems aloud and capture mistakes in a learning log.",
                "Connect each practice topic to the target role's interview expectations.",
            ],
        },
        {
            "phase": "Interview and application readiness",
            "duration_days": interview_days,
            "tasks": [
                "Complete role-specific mock interviews.",
                "Prepare project explanation, trade-offs, and debugging stories.",
                "Apply only to roles whose requirements match the updated readiness score.",
            ],
        },
    ]

    return {
        "plan_phases": phases,
        "first_project_assignment": project,
        "mock_interview_questions": [
            "Walk me through your strongest project and explain the hardest technical decision.",
            "What would you improve if you had one more week on this project?",
            "Explain one bug you faced and how you debugged it.",
            "Which target-role skill is currently your weakest, and what proof will you build for it?",
        ],
    }


def adapt_plan_from_progress(
    diagnosis_result: dict[str, Any],
    progress_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Adapt the plan based on completed, blocked, and in-progress tasks."""
    if not progress_tasks:
        return {
            "adaptation": "no_progress_yet",
            "recommended_change": "Keep the current plan, but add the first three measurable tasks.",
            "duration_adjustment_days": 0,
            "next_actions": [
                "Add one profile repair task.",
                "Add one project milestone task.",
                "Add one interview practice task.",
            ],
        }

    total = len(progress_tasks)
    done = sum(1 for task in progress_tasks if task.get("status") == "done")
    blocked = sum(1 for task in progress_tasks if task.get("status") == "blocked")
    in_progress = sum(1 for task in progress_tasks if task.get("status") == "in_progress")
    completion_rate = done / total

    if blocked:
        return {
            "adaptation": "blocked",
            "recommended_change": "Extend the plan and replace blocked work with smaller mentor-reviewable tasks.",
            "duration_adjustment_days": min(14, blocked * 3),
            "next_actions": [
                "Ask the student to explain the blocker in one paragraph.",
                "Split the blocked task into a 60-90 minute subtask.",
                "Schedule a mock review before assigning new advanced work.",
            ],
        }

    if completion_rate >= 0.8:
        return {
            "adaptation": "ahead",
            "recommended_change": "Keep duration stable and increase project quality bar instead of adding random topics.",
            "duration_adjustment_days": 0,
            "next_actions": [
                "Add tests or validation to the main project.",
                "Improve deployment and README proof.",
                "Run a role-specific mock interview.",
            ],
        }

    if completion_rate < 0.4 and in_progress == 0:
        return {
            "adaptation": "behind",
            "recommended_change": "Extend the plan and reduce scope to one proof-of-work project plus core interview basics.",
            "duration_adjustment_days": 7,
            "next_actions": [
                "Remove low-impact optional tasks.",
                "Focus on the highest-weight readiness gap.",
                "Assign one small deliverable due this week.",
            ],
        }

    return {
        "adaptation": "on_track",
        "recommended_change": "Keep the current plan and continue weekly evaluation.",
        "duration_adjustment_days": 0,
        "next_actions": [
            "Review the active project milestone.",
            "Update resume proof after each completed deliverable.",
            "Run another mock interview after two more completed tasks.",
        ],
    }
