document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  if (getToken() && (location.pathname.endsWith("index.html") || location.pathname === "/")) {
    window.location.href = "/dashboard.html";
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const error = document.getElementById("authError");
      error.textContent = "";
      try {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: loginForm.email.value.trim(),
            password: loginForm.password.value,
          }),
        });
        setSession(data.access_token, data.user);
        window.location.href = "/dashboard.html";
      } catch (err) {
        error.textContent = err.message;
      }
    });
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const error = document.getElementById("authError");
      error.textContent = "";
      try {
        const data = await api("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({
            full_name: registerForm.full_name.value.trim(),
            email: registerForm.email.value.trim(),
            password: registerForm.password.value,
          }),
        });
        setSession(data.access_token, data.user);
        window.location.href = "/dashboard.html";
      } catch (err) {
        error.textContent = err.message;
      }
    });
  }
});
