from __future__ import annotations

from typing import Any

from skillbridge_agent.tools.diagnosis_tools import ROLE_MARKET_REQUIREMENTS


BASE_TEST = {
    "coding": {
        "prompt": "Write a function `find_two_sum(nums, target)` that returns the indices of two numbers whose sum equals target. Explain the time complexity in a comment.",
        "keywords": ["def", "for", "return", "target", "dict", "map", "enumerate", "complexity", "o("],
    },
    "dsa": {
        "prompt": "You are given an array with duplicates. Explain how you would find the first non-repeating element efficiently.",
        "keywords": ["hash", "dict", "map", "count", "frequency", "order", "o(n)"],
    },
    "communication": {
        "prompt": "Explain your strongest project to an interviewer in 5-7 lines. Include the problem, your role, technical choices, and measurable outcome.",
        "keywords": ["problem", "built", "used", "because", "result", "learned", "improved"],
    },
    "aptitude": {
        "prompt": "A task takes 6 students 8 days. How many days will 12 students take at the same rate?",
        "options": ["2", "4", "8", "16"],
        "answer": "4",
    },
}


ROLE_TESTS: dict[str, dict[str, Any]] = {
    "backend_developer": {
        "coding": {
            "prompt": "Write a REST API handler/pseudocode for creating a job application record with validation for title, company, status, and user id.",
            "keywords": ["post", "api", "validate", "title", "company", "status", "user", "database", "return"],
        },
        "role_questions": [
            {
                "id": "backend_http",
                "skill": "REST APIs",
                "prompt": "Which HTTP status code is most suitable after successfully creating a resource?",
                "options": ["200", "201", "301", "404"],
                "answer": "201",
            },
            {
                "id": "backend_sql",
                "skill": "SQL",
                "prompt": "Which SQL clause filters rows before grouping?",
                "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
                "answer": "WHERE",
            },
            {
                "id": "backend_auth",
                "skill": "authentication",
                "prompt": "Which token format is commonly used for stateless API authentication?",
                "options": ["JWT", "CSV", "HTML", "PNG"],
                "answer": "JWT",
            },
        ],
    },
    "frontend_developer": {
        "coding": {
            "prompt": "Write a React component/pseudocode that fetches internships from an API and renders loading, error, and empty states.",
            "keywords": ["useState", "useEffect", "fetch", "loading", "error", "map", "return"],
        },
        "role_questions": [
            {
                "id": "frontend_state",
                "skill": "React",
                "prompt": "Which React hook stores local component state?",
                "options": ["useState", "useMemo", "useRef", "useId"],
                "answer": "useState",
            },
            {
                "id": "frontend_accessibility",
                "skill": "responsive UI",
                "prompt": "Which attribute gives an accessible label to an icon-only button?",
                "options": ["aria-label", "src", "href", "target"],
                "answer": "aria-label",
            },
            {
                "id": "frontend_api",
                "skill": "API integration",
                "prompt": "Which browser API is commonly used to make HTTP requests?",
                "options": ["fetch", "canvas", "localStorage", "history"],
                "answer": "fetch",
            },
        ],
    },
    "data_analyst": {
        "coding": {
            "prompt": "Write SQL to calculate applications per status from a table `applications(status, created_at)` grouped by status.",
            "keywords": ["select", "count", "from", "group by", "status"],
        },
        "role_questions": [
            {
                "id": "data_join",
                "skill": "SQL",
                "prompt": "Which join keeps all rows from the left table?",
                "options": ["LEFT JOIN", "INNER JOIN", "CROSS JOIN", "SELF JOIN"],
                "answer": "LEFT JOIN",
            },
            {
                "id": "data_chart",
                "skill": "dashboarding",
                "prompt": "Which chart is best for showing a trend over time?",
                "options": ["Line chart", "Pie chart", "Treemap", "Gauge"],
                "answer": "Line chart",
            },
            {
                "id": "data_metric",
                "skill": "business communication",
                "prompt": "A good insight should connect data to what?",
                "options": ["Decision/action", "Font size", "File name", "Random color"],
                "answer": "Decision/action",
            },
        ],
    },
    "qa_engineer": {
        "coding": {
            "prompt": "Write pseudocode or test steps to verify login validation for empty password, wrong password, and successful login.",
            "keywords": ["test", "assert", "empty", "wrong", "success", "expected", "actual"],
        },
        "role_questions": [
            {
                "id": "qa_bug",
                "skill": "bug reports",
                "prompt": "Which item is essential in a bug report?",
                "options": ["Steps to reproduce", "Favorite color", "Laptop price", "Team size"],
                "answer": "Steps to reproduce",
            },
            {
                "id": "qa_api",
                "skill": "API testing",
                "prompt": "Which tool is commonly used for API testing?",
                "options": ["Postman", "Photoshop", "Excel only", "Figma"],
                "answer": "Postman",
            },
            {
                "id": "qa_expected",
                "skill": "test cases",
                "prompt": "A test case should include input, steps, and what?",
                "options": ["Expected result", "Song lyrics", "Logo", "Invoice"],
                "answer": "Expected result",
            },
        ],
    },
    "cloud_devops_beginner": {
        "coding": {
            "prompt": "Write a Dockerfile or deployment steps for a FastAPI app that installs requirements and starts uvicorn on port 8000.",
            "keywords": ["from", "copy", "run", "pip", "requirements", "uvicorn", "port", "cmd"],
        },
        "role_questions": [
            {
                "id": "devops_linux",
                "skill": "Linux",
                "prompt": "Which command lists files in a directory?",
                "options": ["ls", "cd", "ping", "kill"],
                "answer": "ls",
            },
            {
                "id": "devops_docker",
                "skill": "Docker",
                "prompt": "Which file commonly defines image build instructions?",
                "options": ["Dockerfile", "README.md", "package-lock.json", "index.html"],
                "answer": "Dockerfile",
            },
            {
                "id": "devops_ci",
                "skill": "CI/CD",
                "prompt": "CI usually runs automatically after what event?",
                "options": ["Code push", "Mouse click only", "Screen lock", "Battery charge"],
                "answer": "Code push",
            },
        ],
    },
}


def get_assessment_for_role(target_role: str) -> dict[str, Any]:
    role_data = ROLE_TESTS.get(target_role, {})
    market = ROLE_MARKET_REQUIREMENTS.get(target_role, ROLE_MARKET_REQUIREMENTS["software_developer"])
    merged = {
        "target_role": target_role,
        "required_skills": market["skills"],
        "coding": {**BASE_TEST["coding"], **role_data.get("coding", {})},
        "dsa": BASE_TEST["dsa"],
        "communication": BASE_TEST["communication"],
        "aptitude": BASE_TEST["aptitude"],
        "role_questions": role_data.get("role_questions", []),
    }
    return _strip_answers(merged)


def evaluate_assessment(submission: dict[str, Any]) -> dict[str, Any]:
    target_role = submission.get("target_role", "software_developer")
    role_data = ROLE_TESTS.get(target_role, {})
    market = ROLE_MARKET_REQUIREMENTS.get(target_role, ROLE_MARKET_REQUIREMENTS["software_developer"])
    coding = {**BASE_TEST["coding"], **role_data.get("coding", {})}
    dsa = BASE_TEST["dsa"]
    communication = BASE_TEST["communication"]
    aptitude = BASE_TEST["aptitude"]
    role_questions = role_data.get("role_questions", [])

    programming_score = _keyword_score(submission.get("coding_answer", ""), coding["keywords"])
    dsa_score = _keyword_score(submission.get("dsa_answer", ""), dsa["keywords"])
    communication_score = _communication_score(submission.get("communication_answer", ""), communication["keywords"])
    aptitude_score = 100 if submission.get("aptitude_answer") == aptitude["answer"] else 0

    role_answers = submission.get("role_answers", {})
    skill_ratings = []
    for skill in market["skills"]:
        matching_questions = [q for q in role_questions if q["skill"].lower() == skill.lower()]
        if not matching_questions:
            skill_ratings.append({"name": skill, "rating": 0})
            continue
        correct = sum(1 for question in matching_questions if role_answers.get(question["id"]) == question["answer"])
        rating = 5 if correct == len(matching_questions) else 0
        skill_ratings.append({"name": skill, "rating": rating})

    feedback = []
    if programming_score < 60:
        feedback.append("Coding answer needs clearer structure, validation, and implementation details.")
    if dsa_score < 60:
        feedback.append("DSA answer should mention data structures, complexity, and edge cases.")
    if communication_score < 60:
        feedback.append("Project explanation needs problem, role, technical choices, and outcome.")
    if aptitude_score < 60:
        feedback.append("Aptitude answer was incorrect; revisit work-rate basics.")

    return {
        "assessment": {
            "programming_score": programming_score,
            "dsa_score": dsa_score,
            "communication_score": communication_score,
            "aptitude_score": aptitude_score,
            "notes": "Evaluated from role-based test answers.",
        },
        "skill_ratings": skill_ratings,
        "feedback": feedback or ["Assessment answers are strong enough to generate the overall plan."],
    }


def get_task_evaluation(task_title: str, target_role: str) -> dict[str, Any]:
    market = ROLE_MARKET_REQUIREMENTS.get(target_role, ROLE_MARKET_REQUIREMENTS["software_developer"])
    primary_skill = market["skills"][0]
    return {
        "task_title": task_title,
        "target_role": target_role,
        "coding": {
            "prompt": (
                f"For this completed task: '{task_title}', write the core code/pseudocode or command sequence "
                "that proves you can implement it. Include validation or error handling."
            ),
        },
        "concept": {
            "prompt": (
                f"Explain the most important concept behind '{task_title}' for a {target_role.replace('_', ' ')} role. "
                "Mention trade-offs, edge cases, and why it matters."
            ),
        },
        "reflection": {
            "prompt": (
                "Write 4-6 lines on what you completed, what broke, how you debugged it, and what proof you added "
                "to GitHub/resume."
            ),
        },
        "mcq": {
            "prompt": f"Which proof best shows progress on {primary_skill}?",
            "options": [
                "Working implementation with README/tests or screenshots",
                "Only watching a video",
                "Only copying a definition",
                "Leaving the task undocumented",
            ],
        },
    }


def evaluate_task_submission(submission: dict[str, Any]) -> dict[str, Any]:
    coding_score = _task_keyword_score(
        submission.get("coding_answer", ""),
        [
            "code",
            "function",
            "validate",
            "error",
            "return",
            "test",
            "command",
            "run",
            "deploy",
            "api",
            "built",
            "implemented",
            "updated",
            "resume",
            "github",
            "readme",
            "proof",
            "project",
            "pushed",
            "documented",
        ],
    )
    concept_score = _task_keyword_score(
        submission.get("concept_answer", ""),
        [
            "because",
            "trade",
            "edge",
            "case",
            "debug",
            "user",
            "data",
            "security",
            "performance",
            "test",
            "evidence",
            "proof",
            "role",
            "interview",
            "technical",
            "outcome",
        ],
    )
    reflection_score = _task_keyword_score(
        submission.get("reflection_answer", ""),
        ["completed", "broke", "debug", "proof", "github", "readme", "test", "learned"],
    )
    mcq_score = (
        100
        if submission.get("mcq_answer") == "Working implementation with README/tests or screenshots"
        else 30
    )
    score = round((coding_score * 0.35) + (concept_score * 0.25) + (reflection_score * 0.25) + (mcq_score * 0.15))

    passed = score >= 75
    feedback = []
    if not passed:
        if coding_score < 75:
            feedback.append("Add concrete implementation details, commands, validation, tests, or error handling.")
        if concept_score < 75:
            feedback.append("Explain the concept with trade-offs, edge cases, and why it matters in the role.")
        if reflection_score < 75:
            feedback.append("Document what broke, how you debugged it, and what proof was added.")
        if mcq_score < 75:
            feedback.append("Progress must be backed by working proof, not only passive learning.")

    resources = [
        "Revisit the relevant official docs for the tool/framework used in this task.",
        "Find one small tutorial and rebuild the task without copy-pasting.",
        "Add README notes, screenshots, tests, or a short walkthrough before retrying.",
    ]

    return {
        "score": score,
        "passed": passed,
        "feedback": feedback or ["Good work. This task is strong enough to unlock the next one."],
        "resources": [] if passed else resources,
    }


def _keyword_score(answer: str, keywords: list[str]) -> int:
    text = answer.lower()
    word_count = len(text.split())
    if not text.strip():
        return 0
    hits = sum(1 for keyword in keywords if keyword.lower() in text)
    if hits == 0:
        return min(15, word_count // 4)
    length_bonus = min(18, word_count // 5)
    return max(5, min(100, round((hits / max(len(keywords), 1)) * 88 + length_bonus)))


def _task_keyword_score(answer: str, keywords: list[str]) -> int:
    text = answer.lower()
    word_count = len(text.split())
    hits = sum(1 for keyword in keywords if keyword.lower() in text)
    length_bonus = min(20, word_count // 4)
    score = 20 + (hits * 8) + length_bonus
    if word_count < 12:
        score = min(score, 45)
    return max(20, min(100, round(score)))


def _communication_score(answer: str, keywords: list[str]) -> int:
    text = answer.lower()
    word_count = len(text.split())
    if not text.strip():
        return 0
    hits = sum(1 for keyword in keywords if keyword.lower() in text)
    if hits == 0:
        return min(15, word_count // 4)
    length_score = 24 if word_count >= 60 else 12 if word_count >= 30 else 4
    return max(5, min(100, round((hits / max(len(keywords), 1)) * 72 + length_score)))


def _strip_answers(test: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(test)
    cleaned["aptitude"] = {key: value for key, value in test["aptitude"].items() if key != "answer"}
    cleaned["role_questions"] = [
        {key: value for key, value in question.items() if key != "answer"}
        for question in test["role_questions"]
    ]
    return cleaned
