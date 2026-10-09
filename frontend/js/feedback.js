document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  renderNav("feedback");
  const params = new URLSearchParams(location.search);
  let id = params.get("id");

  const interviews = await api("/api/interviews");
  const select = document.getElementById("interviewSelect");
  select.innerHTML = interviews
    .map((item) => `<option value="${item.id}" ${String(item.id) === String(id) ? "selected" : ""}>${item.target_role} · ${item.status}</option>`)
    .join("");
  if (!id && interviews[0]) id = interviews[0].id;
  if (id) await showFeedback(id);

  select.addEventListener("change", async () => {
    await showFeedback(select.value);
    history.replaceState({}, "", `/feedback.html?id=${select.value}`);
  });
});

async function showFeedback(id) {
  const host = document.getElementById("feedbackHost");
  try {
    const data = await api(`/api/interviews/${id}/feedback`);
    host.innerHTML = `
      <div class="card">
        <div class="cat">${data.target_role}</div>
        <p class="score">${data.overall_score}<span style="font-size:18px">/100</span></p>
        <div class="progress"><span style="width:${data.overall_score}%"></span></div>
        <p class="muted">Average across ${data.items.length} scored answers.</p>
      </div>
      ${data.items
        .map(
          (item) => `
        <article class="card" style="margin-top:16px">
          <div class="cat">${item.category} · ${item.score}/100</div>
          <h3>${item.question}</h3>
          <p>${item.answer}</p>
          <div class="grid">
            <div>
              <h4>Strengths</h4>
              <ul class="list">${item.strengths.map((s) => `<li>${s}</li>`).join("")}</ul>
            </div>
            <div>
              <h4>Improve</h4>
              <ul class="list">${item.improvements.map((s) => `<li>${s}</li>`).join("")}</ul>
            </div>
          </div>
          <p class="muted">${item.detailed_feedback}</p>
        </article>
      `
        )
        .join("")}
    `;
  } catch (err) {
    host.innerHTML = `<p class="error">${err.message}</p>`;
  }
}
