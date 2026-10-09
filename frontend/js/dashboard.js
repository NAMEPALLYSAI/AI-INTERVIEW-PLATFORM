document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  renderNav("dashboard");
  const user = getUser();
  document.getElementById("welcome").textContent = `Welcome back, ${user.full_name.split(" ")[0]}.`;

  try {
    const [resumes, interviews] = await Promise.all([
      api("/api/resumes"),
      api("/api/interviews"),
    ]);
    document.getElementById("resumeCount").textContent = resumes.length;
    document.getElementById("interviewCount").textContent = interviews.length;
    const completed = interviews.filter((item) => item.status === "completed").length;
    document.getElementById("completedCount").textContent = completed;

    const list = document.getElementById("recentInterviews");
    if (!interviews.length) {
      list.innerHTML = "<p class='muted'>No interviews yet. Upload a resume, then start a session.</p>";
      return;
    }
    list.innerHTML = interviews
      .slice(0, 5)
      .map(
        (item) => `
        <div class="question">
          <div class="cat">${item.status}</div>
          <h3>${item.target_role}</h3>
          <p class="muted">${new Date(item.created_at).toLocaleString()} · ${item.questions.length} questions</p>
          <a class="btn secondary" href="/interview.html?id=${item.id}">Open questions</a>
          <a class="btn" href="/feedback.html?id=${item.id}">View feedback</a>
        </div>
      `
      )
      .join("");
  } catch (err) {
    document.getElementById("recentInterviews").innerHTML = `<p class="error">${err.message}</p>`;
  }
});
