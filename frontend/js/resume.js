document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  renderNav("resume");
  const form = document.getElementById("uploadForm");
  const statusEl = document.getElementById("uploadStatus");
  await loadResumes();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = form.file.files[0];
    if (!file) {
      statusEl.textContent = "Choose a resume file first.";
      return;
    }
    const body = new FormData();
    body.append("file", file);
    statusEl.textContent = "Reading your resume…";
    try {
      await api("/api/resumes/upload", { method: "POST", body });
      statusEl.textContent = "Uploaded and parsed.";
      form.reset();
      await loadResumes();
    } catch (err) {
      statusEl.textContent = err.message;
    }
  });
});

async function loadResumes() {
  const host = document.getElementById("resumeList");
  try {
    const resumes = await api("/api/resumes");
    if (!resumes.length) {
      host.innerHTML = "<p class='muted'>No resumes uploaded yet.</p>";
      return;
    }
    host.innerHTML = resumes
      .map(
        (resume) => `
        <article class="card">
          <div class="cat">Resume #${resume.id}</div>
          <h3>${resume.original_filename}</h3>
          <p class="muted">${new Date(resume.created_at).toLocaleString()}</p>
          <p>${resume.excerpt || "No extractable text found."}</p>
          <div class="chip-row">
            ${(resume.skills || []).map((skill) => `<span class="chip">${skill}</span>`).join("") || "<span class='muted'>No skills detected yet</span>"}
          </div>
          <p style="margin-top:16px">
            <a class="btn" href="/interview.html?resume_id=${resume.id}">Start interview from this resume</a>
          </p>
        </article>
      `
      )
      .join("");
  } catch (err) {
    host.innerHTML = `<p class="error">${err.message}</p>`;
  }
}
