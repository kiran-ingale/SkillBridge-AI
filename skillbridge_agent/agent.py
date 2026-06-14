import os

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search

from .tools.diagnosis_tools import (
    analyze_github_profile,
    analyze_resume_text,
    adapt_plan_from_progress,
    estimate_plan_duration,
    generate_personalized_plan,
    get_market_requirements,
    score_employability,
)

load_dotenv()
load_dotenv("skillbridge_agent/.env")

MODEL_NAME = os.getenv("SKILLBRIDGE_MODEL", "groq/llama-3.1-8b-instant")
USE_GROQ = MODEL_NAME.startswith("groq/")


def build_model() -> str | LiteLlm:
    if USE_GROQ:
        return LiteLlm(model=MODEL_NAME)
    return MODEL_NAME


MARKET_RESEARCH_TOOLS = [get_market_requirements] if USE_GROQ else [google_search, get_market_requirements]
ROOT_TOOLS = [
    analyze_resume_text,
    analyze_github_profile,
    get_market_requirements,
    score_employability,
    estimate_plan_duration,
    generate_personalized_plan,
    adapt_plan_from_progress,
]
if not USE_GROQ:
    ROOT_TOOLS.insert(0, google_search)

resume_analyst_agent = Agent(
    model=build_model(),
    name="resume_analyst_agent",
    description="Analyzes resumes for job-readiness proof, clarity, and missing employability signals.",
    instruction=(
        "You evaluate Indian engineering student resumes. Be specific, evidence-based, "
        "and practical. Prefer proof-of-work, project impact, role keywords, and clarity "
        "over generic advice."
    ),
    tools=[analyze_resume_text],
)

github_analyst_agent = Agent(
    model=build_model(),
    name="github_analyst_agent",
    description="Analyzes GitHub and project evidence for role readiness.",
    instruction=(
        "Review GitHub/project evidence like a practical mentor. Look for README quality, "
        "deployment, tests, API/database evidence, and whether the project is resume-worthy."
    ),
    tools=[analyze_github_profile],
)

market_research_agent = Agent(
    model=build_model(),
    name="market_research_agent",
    description="Finds current role expectations and converts them into a compact skill rubric.",
    instruction=(
        "Use the role rubric tool to ground the diagnosis. If the runtime later provides a "
        "non-Google web search tool, use current entry-level job and internship requirements "
        "for the target role in India and cite the evidence. With Groq/LiteLLM, treat the "
        "offline role rubric as the MVP fallback."
    ),
    tools=MARKET_RESEARCH_TOOLS,
)

planning_agent = Agent(
    model=build_model(),
    name="personalized_planning_agent",
    description="Estimates realistic plan duration and generates an adaptive employability plan.",
    instruction=(
        "Never force a 30-day roadmap. Estimate the realistic duration from gaps, target role, "
        "weekly available hours, and role requirements. If the user asks for a shorter deadline, "
        "provide a disclaimer and explain the trade-offs."
    ),
    tools=[score_employability, estimate_plan_duration, generate_personalized_plan, adapt_plan_from_progress],
)

SUB_AGENTS = [] if USE_GROQ else [
    resume_analyst_agent,
    github_analyst_agent,
    market_research_agent,
    planning_agent,
]

root_agent = Agent(
    model=build_model(),
    name="skillbridge_root_agent",
    description="Orchestrates SkillBridge AI's multi-agent employability diagnosis and planning pipeline.",
    instruction=(
        "You are SkillBridge AI, an agentic employability coach for Indian engineering students. "
        "Diagnose why a student is not job-ready, use tools and specialist reasoning, ground plans "
        "in resume/GitHub/assessment/market evidence, and create a personalized plan with a "
        "realistic duration. Do not give generic DSA roadmap advice. When a user requests a fixed "
        "deadline shorter than the estimate, include a clear disclaimer and a compressed option."
    ),
    sub_agents=SUB_AGENTS,
    tools=ROOT_TOOLS,
)
