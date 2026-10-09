const TOKEN_KEY = "prepline_token";
const USER_KEY = "prepline_user";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function api(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : detail || "Request failed";
    throw new Error(message);
  }
  return data;
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/index.html";
  }
}

function renderNav(active) {
  const user = getUser();
  const nav = document.getElementById("nav");
  if (!nav) return;
  const links = user
    ? `
      <a href="/dashboard.html" class="${active === "dashboard" ? "on" : ""}">Studio</a>
      <a href="/resume.html" class="${active === "resume" ? "on" : ""}">Resume</a>
      <a href="/interview.html" class="${active === "interview" ? "on" : ""}">Interview</a>
      <a href="/feedback.html" class="${active === "feedback" ? "on" : ""}">Feedback</a>
      <button class="secondary" id="logoutBtn" type="button">Log out</button>
    `
    : `
      <a href="/index.html">Log in</a>
      <a href="/register.html">Create account</a>
    `;
  nav.innerHTML = `
    <a class="brand" href="${user ? "/dashboard.html" : "/index.html"}">Prep<span>Line</span></a>
    <div class="nav-links">${links}</div>
  `;
  const logout = document.getElementById("logoutBtn");
  if (logout) {
    logout.addEventListener("click", () => {
      clearSession();
      window.location.href = "/index.html";
    });
  }
}
