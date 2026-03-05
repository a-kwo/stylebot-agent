// Redirect to chat if already logged in
if (localStorage.getItem("stylebot_token")) {
  redirectAfterAuth(localStorage.getItem("stylebot_token"));
}

async function redirectAfterAuth(token) {
  try {
    const res = await fetch("/api/profile/onboarding-status", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    location.replace(data.onboarded ? "/chat.html" : "/onboarding.html");
  } catch {
    location.replace("/chat.html");
  }
}

function showTab(tab) {
  document.getElementById("form-login").style.display = tab === "login" ? "flex" : "none";
  document.getElementById("form-register").style.display = tab === "register" ? "flex" : "none";
  document.getElementById("tab-login").classList.toggle("active", tab === "login");
  document.getElementById("tab-register").classList.toggle("active", tab === "register");
  document.getElementById("login-error").textContent = "";
  document.getElementById("reg-error").textContent = "";
}

async function authRequest(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";
  btn.disabled = true;
  btn.textContent = "Signing in…";

  try {
    const data = await authRequest("/api/auth/login", {
      username: document.getElementById("login-username").value,
      password: document.getElementById("login-password").value,
    });
    localStorage.setItem("stylebot_token", data.access_token);
    await redirectAfterAuth(data.access_token);
  } catch (err) {
    errEl.textContent = err.message;
    btn.disabled = false;
    btn.textContent = "Sign in";
  }
});

document.getElementById("form-register").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  const errEl = document.getElementById("reg-error");
  errEl.textContent = "";
  btn.disabled = true;
  btn.textContent = "Creating account…";

  try {
    const data = await authRequest("/api/auth/register", {
      username: document.getElementById("reg-username").value,
      password: document.getElementById("reg-password").value,
    });
    localStorage.setItem("stylebot_token", data.access_token);
    await redirectAfterAuth(data.access_token);
  } catch (err) {
    errEl.textContent = err.message;
    btn.disabled = false;
    btn.textContent = "Create account";
  }
});
