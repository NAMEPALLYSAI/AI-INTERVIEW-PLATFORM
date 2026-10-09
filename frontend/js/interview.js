document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  renderNav("interview");
  const params = new URLSearchParams(location.search);
  const id = params.get("id");
  const resumeId = params.get("resume_id");

  await populateResumes(resumeId);
  if (id) {
    await loadInterview(id);
  }

  document.getElementById("startForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const error = document.getElementById("startError");
    error.textContent = "";
    const resumeValue = document.getElementById("resumeId").value;
    try {
      const interview = await api("/api/interviews/start", {
        method: "POST",
        body: JSON.stringify({
          target_role: document.getElementById("targetRole").value.trim(),
          resume_id: resumeValue ? Number(resumeValue) : null,
        }),
      });
      history.replaceState({}, "", `/interview.html?id=${interview.id}`);
      renderQuestions(interview);
    } catch (err) {
      error.textContent = err.message;
    }
  });
});

async function populateResumes(selected) {
  const select = document.getElementById("resumeId");
  const resumes = await api("/api/resumes");
  select.innerHTML = `<option value="">No resume (general questions)</option>` + resumes
    .map((resume) => `<option value="${resume.id}" ${String(resume.id) === String(selected) ? "selected" : ""}>${resume.original_filename}</option>`)
    .join("");
}

async function loadInterview(id) {
  const interview = await api(`/api/interviews/${id}`);
  document.getElementById("targetRole").value = interview.target_role;
  renderQuestions(interview);
}

function renderQuestions(interview) {
  const host = document.getElementById("questionList");
  document.getElementById("sessionTitle").textContent = `${interview.target_role} · ${interview.status.replace("_", " ")}`;
  host.innerHTML = interview.questions
    .map(
      (question) => `
      <article class="question" data-qid="${question.id}">
        <div class="cat">${question.category} ${question.answered ? "· saved" : ""}</div>
        <h3>${question.prompt}</h3>
        <label for="a-${question.id}">Your answer</label>
        <textarea id="a-${question.id}" placeholder="Write as if you were speaking in the interview. Aim for 80–150 words."></textarea>
        <button type="button" data-submit="${question.id}">Save answer</button>
        <span class="muted" id="s-${question.id}"></span>
      </article>
    `
    )
    .join("");

  host.querySelectorAll("[data-submit]").forEach((button) => {
    button.addEventListener("click", async () => {
      const questionId = button.getAttribute("data-submit");
      const text = document.getElementById(`a-${questionId}`).value.trim();
      const status = document.getElementById(`s-${questionId}`);
      status.textContent = "Scoring…";
      try {
        const result = await api(`/api/interviews/${interview.id}/questions/${questionId}/answer`, {
          method: "POST",
          body: JSON.stringify({ answer_text: text }),
        });
        status.textContent = "Saved. Feedback is ready.";
        if (result.interview_status === "completed") {
          document.getElementById("sessionTitle").textContent = `${interview.target_role} · completed`;
        }
      } catch (err) {
        status.textContent = err.message;
      }
    });
  });

  document.getElementById("feedbackLink").href = `/feedback.html?id=${interview.id}`;
  document.getElementById("feedbackLink").hidden = false;
}
