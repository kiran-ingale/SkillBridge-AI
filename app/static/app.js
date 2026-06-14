const authScreen = document.querySelector("#authScreen");
const workspace = document.querySelector("#workspace");
const authForm = document.querySelector("#authForm");
const authSubmit = document.querySelector("#authSubmit");
const authMessage = document.querySelector("#authMessage");
const logoutBtn = document.querySelector("#logoutBtn");
const chatToggleBtn = document.querySelector("#chatToggleBtn");
const closeChatBtn = document.querySelector("#closeChatBtn");
const chatDrawer = document.querySelector("#chatDrawer");
const pageTitle = document.querySelector("#pageTitle");
const profileForm = document.querySelector("#profileForm");
const testForm = document.querySelector("#testForm");
const parseResumeBtn = document.querySelector("#parseResumeBtn");
const resumeFile = document.querySelector("#resumeFile");
const targetRole = document.querySelector("#targetRole");
const testQuestions = document.querySelector("#testQuestions");
const testRoleLabel = document.querySelector("#testRoleLabel");
const startMockInterviewBtn = document.querySelector("#startMockInterviewBtn");
const coachChatForm = document.querySelector("#coachChatForm");
const coachChatInput = document.querySelector("#coachChatInput");
const chatMessages = document.querySelector("#chatMessages");
const profileCardName = document.querySelector("#profileCardName");
const profileCardGithub = document.querySelector("#profileCardGithub");
const profileCardLinkedin = document.querySelector("#profileCardLinkedin");

const state = {
  authMode: "login",
  user: null,
  token: localStorage.getItem("skillbridge_token") || null,
  profile: null,
  profileDiagnosis: null,
  overallReport: null,
  currentTest: null,
  latestEvaluation: null,
  mockInterview: null,
  mockTimerId: null,
  chatHistory: [],
  execution: {
    phaseIndex: null,
    phase: null,
    tasks: [],
    activeTaskIndex: null,
  },
};

const stepTitles = {
  profile: "Student profile",
  diagnosis: "Profile diagnosis",
  test: "Skill test",
  plan: "Plan & mentor",
  mock: "Mock interview",
  execute: "Execute plan",
};

const roleSkillMap = {
  backend_developer: ["REST APIs", "SQL", "authentication", "deployment", "testing", "Git"],
  frontend_developer: ["HTML/CSS", "JavaScript", "React", "responsive UI", "API integration", "deployment"],
  data_analyst: ["SQL", "Excel", "Python", "statistics", "dashboarding", "business communication"],
  qa_engineer: ["manual testing", "test cases", "bug reports", "automation basics", "API testing", "SDLC"],
  software_developer: ["programming fundamentals", "DSA", "Git", "projects", "debugging", "communication"],
  embedded_iot_engineer: ["C/C++", "microcontrollers", "sensors", "serial communication", "debugging", "documentation"],
  cloud_devops_beginner: ["Linux", "networking basics", "Docker", "CI/CD", "cloud deployment", "monitoring"],
};

function showWorkspace() {
  loadSavedProfile();
  updateProfileCard();
  authScreen.classList.add("hidden");
  workspace.classList.remove("hidden");
  showStep("profile");
}

function showStep(step) {
  document.querySelectorAll(".view").forEach((view) => view.classList.add("hidden"));
  document.querySelector(`#${step}View`).classList.remove("hidden");
  document.querySelectorAll(".step").forEach((button) => {
    button.classList.toggle("active", button.dataset.step === step);
  });
  pageTitle.textContent = stepTitles[step];
}

function numberValue(formData, key, fallback = 0) {
  const raw = formData.get(key);
  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

function textValue(formData, key) {
  return String(formData.get(key) || "").trim();
}

function listItems(target, items) {
  target.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  });
}

function roleLabel(role) {
  return role.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function showAuthMessage(message, type = "error") {
  authMessage.classList.remove("hidden", "success");
  authMessage.classList.toggle("success", type === "success");
  authMessage.textContent = message;
}

function profileStorageKey() {
  const email = state.user?.email || localStorage.getItem("skillbridge_email") || "guest";
  return `skillbridge_profile_${email}`;
}

function saveProfileLocally(profile) {
  localStorage.setItem(profileStorageKey(), JSON.stringify(profile));
}

function loadSavedProfile() {
  const saved = localStorage.getItem(profileStorageKey());
  if (!saved) {
    state.profile = state.profile || buildProfilePayload();
    return;
  }
  try {
    const profile = JSON.parse(saved);
    state.profile = profile;
    fillProfileForm(profile);
  } catch {
    state.profile = state.profile || buildProfilePayload();
  }
}

function fillProfileForm(profile) {
  Object.entries(profile || {}).forEach(([key, value]) => {
    const field = profileForm.elements.namedItem(key);
    if (!field || value === null || Array.isArray(value) || typeof value === "object") return;
    field.value = value;
  });
}

function updateProfileCard() {
  const profile = state.profile || buildProfilePayload();
  profileCardName.textContent = profile.name || state.user?.email || "Student";
  setProfileLink(profileCardGithub, profile.github_url, "GitHub not saved");
  setProfileLink(profileCardLinkedin, profile.linkedin_url, "LinkedIn not saved");
}

function setProfileLink(element, url, fallback) {
  if (url) {
    element.href = url;
    element.textContent = url.replace(/^https?:\/\//, "");
    element.classList.remove("disabled-link");
  } else {
    element.href = "#";
    element.textContent = fallback;
    element.classList.add("disabled-link");
  }
}

async function submitAuth() {
  const formData = new FormData(authForm);
  const endpoint = state.authMode === "signup" ? "/auth/signup" : "/auth/login";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: textValue(formData, "email"),
      password: textValue(formData, "password"),
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(formatApiError(data));
  state.user = data;
  state.token = data.token;
  localStorage.setItem("skillbridge_token", data.token);
  localStorage.setItem("skillbridge_email", data.email);
  return data;
}

async function loadRoleTest(role) {
  testRoleLabel.textContent = roleLabel(role);
  testQuestions.innerHTML = `<div class="report-placeholder">Loading ${roleLabel(role)} test...</div>`;
  const response = await fetch(`/assessment/${role}`);
  const data = await response.json();
  if (!response.ok) throw new Error(formatApiError(data));
  state.currentTest = data;
  renderRoleTest(data);
}

function renderRoleTest(test) {
  const roleQuestions = test.role_questions || [];
  testQuestions.innerHTML = `
    <section class="question-block">
      <div class="question-heading">
        <h2>Coding task</h2>
        <span>Programming</span>
      </div>
      <p>${test.coding.prompt}</p>
      <textarea name="coding_answer" rows="9" placeholder="Write code or detailed pseudocode here."></textarea>
    </section>

    <section class="question-block">
      <div class="question-heading">
        <h2>DSA / problem solving</h2>
        <span>Reasoning</span>
      </div>
      <p>${test.dsa.prompt}</p>
      <textarea name="dsa_answer" rows="5" placeholder="Explain approach, data structure, complexity, and edge cases."></textarea>
    </section>

    <section class="question-block">
      <div class="question-heading">
        <h2>Communication</h2>
        <span>Interview answer</span>
      </div>
      <p>${test.communication.prompt}</p>
      <textarea name="communication_answer" rows="6" placeholder="Write your spoken-style project explanation."></textarea>
    </section>

    <section class="question-block">
      <div class="question-heading">
        <h2>Aptitude</h2>
        <span>Work rate</span>
      </div>
      <p>${test.aptitude.prompt}</p>
      <div class="option-grid">
        ${test.aptitude.options.map((option) => radioOption("aptitude_answer", option)).join("")}
      </div>
    </section>

    <section class="question-block">
      <div class="question-heading">
        <h2>Role-specific skills</h2>
        <span>${roleQuestions.length} questions</span>
      </div>
      <div class="role-question-list">
        ${roleQuestions.map((question) => roleQuestion(question)).join("")}
      </div>
    </section>
  `;
}

function radioOption(name, value) {
  return `
    <label class="choice">
      <input type="radio" name="${name}" value="${value}" required />
      <span>${value}</span>
    </label>
  `;
}

function roleQuestion(question) {
  return `
    <fieldset class="role-question">
      <legend>${question.prompt}</legend>
      <div class="option-grid">
        ${question.options.map((option) => radioOption(`role_${question.id}`, option)).join("")}
      </div>
    </fieldset>
  `;
}

function buildProfilePayload(assessmentOverride = null, skillRatingsOverride = null) {
  const formData = new FormData(profileForm);
  const requestedDuration = numberValue(formData, "requested_duration_days", 0);
  const githubUrl = textValue(formData, "github_url");
  const linkedinUrl = textValue(formData, "linkedin_url");

  return {
    name: textValue(formData, "name"),
    branch: textValue(formData, "branch"),
    academic_year: textValue(formData, "academic_year"),
    location: textValue(formData, "location") || "India",
    target_role: textValue(formData, "target_role"),
    weekly_available_hours: numberValue(formData, "weekly_available_hours", 12),
    requested_duration_days: requestedDuration > 0 ? requestedDuration : null,
    resume_text: textValue(formData, "resume_text"),
    github_url: githubUrl || null,
    linkedin_url: linkedinUrl || null,
    project_description: textValue(formData, "project_description"),
    self_rated_skills: skillRatingsOverride || [],
    assessment:
      assessmentOverride || {
        programming_score: 0,
        dsa_score: 0,
        communication_score: 0,
        aptitude_score: 0,
        notes: "Profile-only diagnosis before target-role skill test.",
      },
  };
}

function buildAssessmentSubmission() {
  const formData = new FormData(testForm);
  const roleAnswers = {};
  (state.currentTest?.role_questions || []).forEach((question) => {
    roleAnswers[question.id] = textValue(formData, `role_${question.id}`);
  });

  return {
    target_role: targetRole.value,
    coding_answer: textValue(formData, "coding_answer"),
    dsa_answer: textValue(formData, "dsa_answer"),
    communication_answer: textValue(formData, "communication_answer"),
    aptitude_answer: textValue(formData, "aptitude_answer"),
    role_answers: roleAnswers,
  };
}

async function evaluateSkillTest() {
  const response = await fetch("/assessment/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildAssessmentSubmission()),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(formatApiError(data));
  return data;
}

async function runDiagnosis(payload) {
  const response = await fetch("/diagnose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(formatApiError(data));
  return data;
}

function formatApiError(data) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : "";
        return location ? `${location}: ${item.msg}` : item.msg;
      })
      .join("\n");
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail, null, 2);
  }
  return "Diagnosis failed";
}

function scoreMetrics(data) {
  return `
    <div class="score-row">
      <div class="metric"><span>Employability</span><strong>${data.employability_score}</strong></div>
      <div class="metric"><span>Role readiness</span><strong>${data.role_readiness_score}</strong></div>
      <div class="metric duration"><span>Estimated plan</span><strong>${data.recommended_duration_days} days</strong></div>
    </div>
  `;
}

function renderReport(target, data, options = {}) {
  const warning = data.deadline_disclaimer ? `<div class="warning">${data.deadline_disclaimer}</div>` : "";
  target.innerHTML = `
    ${scoreMetrics(data)}
    ${warning}
    ${renderEvidenceReview(data.evidence_review)}
    <div class="report-grid">
      <section class="result-block">
        <h2>Top gaps</h2>
        <ul>${(data.top_gaps || []).map((gap) => `<li>${gap}</li>`).join("")}</ul>
      </section>
      <section class="result-block">
        <h2>Market signals</h2>
        <ul>${(data.market_signals || []).map((signal) => `<li>${signal}</li>`).join("")}</ul>
      </section>
    </div>
    ${options.includePlan ? renderPlan(data.plan_phases || []) : ""}
  `;
}

function renderEvidenceReview(evidence) {
  if (!evidence) return "";
  const github = evidence.github || {};
  const linkedin = evidence.linkedin || {};
  const repos = github.repos_reviewed || [];
  return `
    <section class="result-block full">
      <div class="section-title">
        <h2>GitHub and LinkedIn evidence</h2>
        <span>Used in diagnosis</span>
      </div>
      <div class="evidence-grid">
        <article class="evidence-card">
          <div class="phase-header">
            <span>GitHub</span>
            <span class="phase-days">${github.score ?? 0}/100</span>
          </div>
          <p>Source: ${github.source || "not provided"}</p>
          ${
            repos.length
              ? `<ul>${repos
                  .map(
                    (repo) =>
                      `<li>${repo.name || "Repository"}${repo.language ? ` (${repo.language})` : ""} - README: ${
                        repo.has_readme ? "yes" : "no"
                      }, tests: ${repo.has_tests ? "yes" : "no"}</li>`,
                  )
                  .join("")}</ul>`
              : `<p class="muted-text">No public repositories were reviewed. Add a valid GitHub profile/repo URL for stronger proof.</p>`
          }
        </article>
        <article class="evidence-card">
          <div class="phase-header">
            <span>LinkedIn</span>
            <span class="phase-days">${linkedin.score ?? 0}/100</span>
          </div>
          <p>Profile: ${linkedin.handle ? `/in/${linkedin.handle}` : "not provided"}</p>
          <p class="muted-text">${linkedin.inspection_note || "LinkedIn URL was not provided."}</p>
        </article>
      </div>
    </section>
  `;
}

function renderPlan(phases) {
  return `
    <section class="result-block full">
      <div class="section-title">
        <h2>Personalized executable plan</h2>
        <span>Run each phase as todos</span>
      </div>
      <div class="timeline">
        ${phases
          .map((phase, index) => phaseCard(phase, index))
          .join("")}
      </div>
    </section>
  `;
}

function phaseCard(phase, index) {
  return `
    <article class="phase">
      <div class="phase-header">
        <span>${phase.phase}</span>
        <span class="phase-days">${phase.duration_days} days</span>
      </div>
      <ul class="todo-preview">
        ${(phase.tasks || [])
          .map(
            (task, taskIndex) => `<li><span class="todo-index">${taskIndex + 1}</span>${task}</li>`,
          )
          .join("")}
      </ul>
      <button class="secondary execute-phase" type="button" data-phase-index="${index}">Execute this phase</button>
    </article>
  `;
}

function renderMentor(data) {
  document.querySelector("#mentorPanel").classList.remove("hidden");
  document.querySelector("#diagnosisId").textContent = data.diagnosis_id || "not saved";
  document.querySelector("#projectTitle").textContent = data.first_project_assignment?.title || "";
  listItems(document.querySelector("#projectCriteria"), data.first_project_assignment?.acceptance_criteria || []);
}

function openExecutionPhase(phaseIndex) {
  const phases = state.overallReport?.plan_phases || [];
  const phase = phases[phaseIndex];
  if (!phase) return;

  state.execution = {
    phaseIndex,
    phase,
    activeTaskIndex: null,
    tasks: (phase.tasks || []).map((task, index) => ({
      title: task,
      completed: false,
      locked: index !== 0,
      attempts: 0,
      lastScore: null,
      feedback: [],
      resources: [],
    })),
  };

  document.querySelector("#executionTitle").textContent = phase.phase;
  document.querySelector("#taskEvaluationPanel").classList.add("hidden");
  renderExecutionTasks();
  showStep("execute");
}

function renderExecutionTasks() {
  const target = document.querySelector("#executionTasks");
  const tasks = state.execution.tasks;
  if (!tasks.length) {
    target.innerHTML = `<div class="report-placeholder">No tasks found for this phase.</div>`;
    updateExecutionProgress();
    return;
  }

  target.innerHTML = tasks
    .map((task, index) => {
      const status = task.completed ? "Completed" : task.locked ? "Locked" : "Ready";
      const score = task.lastScore === null ? "" : `<span class="task-score">Last score: ${task.lastScore}</span>`;
      return `
        <article class="task-card ${task.locked ? "locked" : ""} ${task.completed ? "done" : ""}">
          <label class="task-check">
            <input type="checkbox" data-task-index="${index}" ${task.completed ? "checked" : ""} ${task.locked ? "disabled" : ""} />
            <span>
              <strong>${task.title}</strong>
              <small>${status}</small>
            </span>
          </label>
          ${score}
          ${task.feedback.length ? `<ul class="task-feedback">${task.feedback.map((item) => `<li>${item}</li>`).join("")}</ul>` : ""}
          ${task.resources.length ? `<div class="resource-box"><strong>Try these before retrying:</strong><ul>${task.resources.map((item) => `<li>${item}</li>`).join("")}</ul></div>` : ""}
        </article>
      `;
    })
    .join("");

  updateExecutionProgress();
}

function updateExecutionProgress() {
  const tasks = state.execution.tasks;
  const completed = tasks.filter((task) => task.completed).length;
  const total = tasks.length;
  const percent = total ? Math.round((completed / total) * 100) : 0;
  document.querySelector("#executionProgressText").textContent = `${completed} of ${total} tasks`;
  document.querySelector("#executionProgressFill").style.width = `${percent}%`;
}

async function openTaskEvaluation(taskIndex) {
  const task = state.execution.tasks[taskIndex];
  if (!task || task.locked || task.completed) return;

  state.execution.activeTaskIndex = taskIndex;
  const panel = document.querySelector("#taskEvaluationPanel");
  panel.classList.remove("hidden");
  panel.innerHTML = `<div class="report-placeholder">Generating evaluation for task ${taskIndex + 1}...</div>`;

  const response = await fetch("/task-evaluation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task_title: task.title,
      target_role: state.overallReport?.target_role || state.profile?.target_role || targetRole.value,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(formatApiError(data));
  renderTaskEvaluationForm(taskIndex, data);
}

function renderTaskEvaluationForm(taskIndex, test) {
  const panel = document.querySelector("#taskEvaluationPanel");
  panel.innerHTML = `
    <form id="taskEvaluationForm" class="task-evaluation-form">
      <div class="question-heading">
        <h2>Evaluation required for task ${taskIndex + 1}</h2>
        <span>Need 75+ to unlock next task</span>
      </div>
      <p class="project-title">${test.task_title}</p>

      <section class="question-block">
        <h2>Coding / implementation proof</h2>
        <p>${test.coding.prompt}</p>
        <textarea name="coding_answer" rows="6" required></textarea>
      </section>

      <section class="question-block">
        <h2>Concept check</h2>
        <p>${test.concept.prompt}</p>
        <textarea name="concept_answer" rows="5" required></textarea>
      </section>

      <section class="question-block">
        <h2>Completion reflection</h2>
        <p>${test.reflection.prompt}</p>
        <textarea name="reflection_answer" rows="5" required></textarea>
      </section>

      <section class="question-block">
        <h2>Proof check</h2>
        <p>${test.mcq.prompt}</p>
        <div class="option-grid">
          ${test.mcq.options.map((option) => radioOption("mcq_answer", option)).join("")}
        </div>
      </section>

      <button class="primary" type="submit">Submit evaluation</button>
    </form>
  `;
}

async function submitTaskEvaluation(event) {
  event.preventDefault();
  const form = event.target;
  const taskIndex = state.execution.activeTaskIndex;
  const task = state.execution.tasks[taskIndex];
  const formData = new FormData(form);
  const submit = form.querySelector(".primary");
  submit.disabled = true;
  submit.textContent = "Evaluating";

  try {
    const response = await fetch("/task-evaluation/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_title: task.title,
        target_role: state.overallReport?.target_role || state.profile?.target_role || targetRole.value,
        coding_answer: textValue(formData, "coding_answer"),
        concept_answer: textValue(formData, "concept_answer"),
        reflection_answer: textValue(formData, "reflection_answer"),
        mcq_answer: textValue(formData, "mcq_answer"),
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(formatApiError(result));

    task.attempts += 1;
    task.lastScore = result.score;
    task.feedback = result.feedback || [];
    task.resources = result.resources || [];

    if (result.passed) {
      task.completed = true;
      task.locked = false;
      const next = state.execution.tasks[taskIndex + 1];
      if (next) next.locked = false;
      document.querySelector("#taskEvaluationPanel").innerHTML = `
        <div class="success-box">
          <h2>Task passed with ${result.score}/100</h2>
          <p>You can now continue to the next task.</p>
        </div>
      `;
    } else {
      task.completed = false;
      task.locked = false;
      document.querySelector("#taskEvaluationPanel").innerHTML = `
        <div class="warning">
          Score: ${result.score}/100. You need 75+ to proceed. Review the resources, improve the same task, then tick it again to retry.
        </div>
      `;
    }
    renderExecutionTasks();
  } catch (error) {
    alert(error.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Submit evaluation";
  }
}

function profileSummary() {
  const profile = state.profile || buildProfilePayload();
  return [
    profile.name,
    profile.branch,
    profile.academic_year,
    profile.location,
    roleLabel(profile.target_role || targetRole.value),
    profile.resume_text,
  ]
    .filter(Boolean)
    .join(" | ")
    .slice(0, 1200);
}

async function startMockInterview() {
  const area = document.querySelector("#mockInterviewArea");
  area.innerHTML = `<div class="report-placeholder">Preparing AI interview...</div>`;
  startMockInterviewBtn.disabled = true;
  startMockInterviewBtn.textContent = "Preparing";
  try {
    const response = await fetch("/mock-interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_role: state.overallReport?.target_role || state.profile?.target_role || targetRole.value,
        profile_summary: profileSummary(),
        project_summary:
          state.overallReport?.first_project_assignment?.title ||
          state.profile?.project_description ||
          textValue(new FormData(profileForm), "project_description"),
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(formatApiError(data));
    state.mockInterview = data;
    renderMockInterview(data);
    startMockTimer(data.duration_minutes || 16);
  } catch (error) {
    area.innerHTML = `<div class="warning">${error.message}</div>`;
  } finally {
    startMockInterviewBtn.disabled = false;
    startMockInterviewBtn.textContent = "Restart interview";
  }
}

function renderMockInterview(interview) {
  const area = document.querySelector("#mockInterviewArea");
  area.className = "";
  area.innerHTML = `
    <form id="mockInterviewForm" class="form-grid">
      <div class="section-title">
        <h2>${interview.duration_minutes}-minute mock interview</h2>
        <span>Technical + communication</span>
      </div>
      ${(interview.questions || [])
        .map(
          (question, index) => `
            <section class="question-block">
              <div class="question-heading">
                <h2>Question ${index + 1}</h2>
                <span>${question.category}</span>
              </div>
              <p>${question.question}</p>
              <textarea name="${question.id}" rows="5" placeholder="Answer as if speaking in an interview." required></textarea>
            </section>
          `,
        )
        .join("")}
      <button class="primary" type="submit">Submit interview for AI evaluation</button>
    </form>
  `;
}

function startMockTimer(minutes) {
  clearInterval(state.mockTimerId);
  let remaining = Math.max(1, minutes) * 60;
  const timer = document.querySelector("#mockTimer");
  const render = () => {
    const mins = String(Math.floor(remaining / 60)).padStart(2, "0");
    const secs = String(remaining % 60).padStart(2, "0");
    timer.textContent = `${mins}:${secs}`;
  };
  render();
  state.mockTimerId = setInterval(() => {
    remaining = Math.max(0, remaining - 1);
    render();
    if (remaining === 0) clearInterval(state.mockTimerId);
  }, 1000);
}

async function submitMockInterview(event) {
  event.preventDefault();
  const form = event.target;
  const submit = form.querySelector(".primary");
  const formData = new FormData(form);
  const answers = {};
  (state.mockInterview?.questions || []).forEach((question) => {
    answers[question.id] = textValue(formData, question.id);
  });

  submit.disabled = true;
  submit.textContent = "AI evaluating";
  try {
    const response = await fetch("/mock-interview/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_role: state.overallReport?.target_role || state.profile?.target_role || targetRole.value,
        questions: state.mockInterview?.questions || [],
        answers,
        profile_summary: profileSummary(),
        project_summary:
          state.overallReport?.first_project_assignment?.title ||
          state.profile?.project_description ||
          textValue(new FormData(profileForm), "project_description"),
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(formatApiError(result));
    renderMockInterviewResult(result);
  } catch (error) {
    document.querySelector("#mockInterviewArea").insertAdjacentHTML("beforeend", `<div class="warning">${error.message}</div>`);
  } finally {
    submit.disabled = false;
    submit.textContent = "Submit interview for AI evaluation";
  }
}

function renderMockInterviewResult(result) {
  clearInterval(state.mockTimerId);
  const verdict = result.passed ? "Passed" : "Not passed yet";
  const boxClass = result.passed ? "success-box" : "warning";
  document.querySelector("#mockInterviewArea").innerHTML = `
    <div class="${boxClass}">
      <h2>${verdict}: ${result.score}/100</h2>
      <p>Technical: ${result.technical_score}/100 | Communication: ${result.communication_score}/100</p>
    </div>
    <section class="result-block full">
      <h2>Improvement plan</h2>
      <ul>${(result.improvement_plan || []).map((item) => `<li>${item}</li>`).join("")}</ul>
    </section>
  `;
}

function buildChatContext() {
  return {
    profile: state.profile || buildProfilePayload(),
    profileDiagnosis: state.profileDiagnosis,
    overallReport: state.overallReport,
    latestEvaluation: state.latestEvaluation,
    mockInterview: state.mockInterview,
    execution: state.execution,
  };
}

function appendChatMessage(role, content) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.textContent = content;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function submitCoachChat(event) {
  event.preventDefault();
  const message = coachChatInput.value.trim();
  if (!message) return;

  appendChatMessage("user", message);
  state.chatHistory.push({ role: "user", content: message });
  coachChatInput.value = "";
  const submit = coachChatForm.querySelector(".primary");
  submit.disabled = true;
  submit.textContent = "Thinking";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        context: buildChatContext(),
        history: state.chatHistory.slice(-8),
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(formatApiError(data));
    appendChatMessage("assistant", data.reply);
    state.chatHistory.push({ role: "assistant", content: data.reply });
  } catch (error) {
    appendChatMessage("assistant", error.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Send";
  }
}

function openChatDrawer() {
  chatDrawer.classList.remove("hidden");
  coachChatInput.focus();
}

function closeChatDrawer() {
  chatDrawer.classList.add("hidden");
}

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    state.authMode = button.dataset.authMode;
    document.querySelectorAll("[data-auth-mode]").forEach((tab) => tab.classList.toggle("active", tab === button));
    authSubmit.textContent = state.authMode === "signup" ? "Create account" : "Login";
    authMessage.classList.add("hidden");
  });
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  authSubmit.disabled = true;
  authSubmit.textContent = state.authMode === "signup" ? "Creating account" : "Checking credentials";
  try {
    const user = await submitAuth();
    showAuthMessage(`Signed in as ${user.email}`, "success");
    showWorkspace();
  } catch (error) {
    showAuthMessage(error.message);
  } finally {
    authSubmit.disabled = false;
    authSubmit.textContent = state.authMode === "signup" ? "Create account" : "Login";
  }
});

logoutBtn.addEventListener("click", () => {
  state.user = null;
  state.token = null;
  localStorage.removeItem("skillbridge_token");
  localStorage.removeItem("skillbridge_email");
  workspace.classList.add("hidden");
  authScreen.classList.remove("hidden");
});

document.querySelectorAll(".step").forEach((button) => {
  button.addEventListener("click", () => showStep(button.dataset.step));
});

document.querySelectorAll("[data-next-step]").forEach((button) => {
  button.addEventListener("click", () => showStep(button.dataset.nextStep));
});

document.addEventListener("click", (event) => {
  const execute = event.target.closest(".execute-phase");
  if (execute) {
    openExecutionPhase(Number(execute.dataset.phaseIndex));
  }
});

document.addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-task-index]");
  if (!checkbox) return;
  const taskIndex = Number(checkbox.dataset.taskIndex);
  const task = state.execution.tasks[taskIndex];
  if (!task || task.locked) return;
  if (checkbox.checked && !task.completed) {
    checkbox.checked = false;
    openTaskEvaluation(taskIndex).catch((error) => alert(error.message));
  }
});

document.addEventListener("submit", (event) => {
  if (event.target.id === "taskEvaluationForm") {
    submitTaskEvaluation(event);
  }
  if (event.target.id === "mockInterviewForm") {
    submitMockInterview(event);
  }
});

startMockInterviewBtn.addEventListener("click", () => {
  startMockInterview();
});

chatToggleBtn.addEventListener("click", () => {
  openChatDrawer();
});

closeChatBtn.addEventListener("click", () => {
  closeChatDrawer();
});

coachChatForm.addEventListener("submit", (event) => {
  submitCoachChat(event);
});

targetRole.addEventListener("change", () => {
  loadRoleTest(targetRole.value).catch((error) => {
    testQuestions.innerHTML = `<div class="warning">${error.message}</div>`;
  });
});

parseResumeBtn.addEventListener("click", async () => {
  const file = resumeFile.files?.[0];
  if (!file) {
    alert("Choose a PDF resume first.");
    return;
  }

  parseResumeBtn.disabled = true;
  parseResumeBtn.textContent = "Parsing";
  try {
    const body = new FormData();
    body.append("file", file);
    const response = await fetch("/resume/parse", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(formatApiError(data));
    profileForm.elements.resume_text.value = data.text;
  } catch (error) {
    alert(error.message);
  } finally {
    parseResumeBtn.disabled = false;
    parseResumeBtn.textContent = "Parse PDF";
  }
});

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = profileForm.querySelector(".primary");
  submit.disabled = true;
  submit.textContent = "Creating diagnosis";
  try {
    state.profile = buildProfilePayload();
    saveProfileLocally(state.profile);
    updateProfileCard();
    state.profileDiagnosis = await runDiagnosis(state.profile);
    renderReport(document.querySelector("#profileReport"), state.profileDiagnosis);
    await loadRoleTest(state.profile.target_role);
    showStep("diagnosis");
  } catch (error) {
    alert(error.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Create profile diagnosis";
  }
});

testForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = testForm.querySelector(".primary");
  submit.disabled = true;
  submit.textContent = "Generating report";
  try {
    state.latestEvaluation = await evaluateSkillTest();
    const payload = buildProfilePayload(state.latestEvaluation.assessment, state.latestEvaluation.skill_ratings);
    saveProfileLocally(payload);
    updateProfileCard();
    state.overallReport = await runDiagnosis(payload);
    renderReport(document.querySelector("#overallReport"), state.overallReport, { includePlan: true });
    renderTestFeedback(state.latestEvaluation.feedback);
    renderMentor(state.overallReport);
    showStep("plan");
  } catch (error) {
    alert(error.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Generate overall report";
  }
});

function renderTestFeedback(feedback) {
  const target = document.querySelector("#overallReport");
  const block = document.createElement("section");
  block.className = "result-block full";
  block.innerHTML = `
    <h2>Test feedback</h2>
    <ul>${(feedback || []).map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
  target.appendChild(block);
}

document.querySelector("#mentorBriefBtn").addEventListener("click", () => {
  const report = state.overallReport;
  if (!report) return;
  const idea = document.querySelector("#projectIdea").value.trim();
  const recommended = report.first_project_assignment?.title || "Build a role-specific proof project.";
  const chosenProject = idea || recommended;
  const role = roleLabel(state.profile?.target_role || targetRole.value);
  const brief = document.querySelector("#mentorBrief");
  brief.classList.remove("hidden");
  brief.innerHTML = `
    <h2>Step-by-step mentor brief</h2>
    <p class="project-title">${chosenProject}</p>
    <ol class="mentor-steps">
      <li>
        <strong>Clarify the outcome.</strong>
        Write one paragraph describing who the project helps, what problem it solves, and why it proves ${role} readiness.
      </li>
      <li>
        <strong>Lock the minimum scope.</strong>
        Choose 3 core features only. For each feature, write the input, output, success condition, and one failure case.
      </li>
      <li>
        <strong>Design before coding.</strong>
        Create the data model, main screens or API routes, folder structure, and a simple flow diagram in the README.
      </li>
      <li>
        <strong>Build the smallest working version.</strong>
        Implement one end-to-end path first, commit it, then add the remaining features one at a time with readable commits.
      </li>
      <li>
        <strong>Add quality proof.</strong>
        Add validation, error handling, test cases or screenshots, and a debugging note explaining one issue you fixed.
      </li>
      <li>
        <strong>Make it recruiter-readable.</strong>
        Update README with setup steps, feature list, tech stack, screenshots/demo link, known limitations, and future improvements.
      </li>
      <li>
        <strong>Prepare interview proof.</strong>
        Write a 90-second explanation covering problem, your role, technical choices, trade-offs, bug fixed, and measurable result.
      </li>
      <li>
        <strong>Final checkpoint.</strong>
        The project is resume-worthy only if another person can open the repo, understand it, run it or view the demo, and see your ownership.
      </li>
    </ol>
  `;
});

loadRoleTest(targetRole.value).catch((error) => {
  testQuestions.innerHTML = `<div class="warning">${error.message}</div>`;
});
