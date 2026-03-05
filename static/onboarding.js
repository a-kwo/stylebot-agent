const token = localStorage.getItem("stylebot_token");
if (!token) location.replace("/");

// If already onboarded, skip to chat
(async () => {
  try {
    const res = await fetch("/api/profile/onboarding-status", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.onboarded) location.replace("/chat.html");
  } catch {}
})();

// ── Helpers ───────────────────────────────────────────────────

async function authFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    localStorage.removeItem("stylebot_token");
    location.replace("/");
    throw new Error("Session expired");
  }
  return res;
}

// ── Phase 1: Demographics form ────────────────────────────────

document.getElementById("onboard-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  const errEl = document.getElementById("onboard-error");
  errEl.textContent = "";
  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    const res = await authFetch("/api/profile/onboard", {
      method: "POST",
      body: JSON.stringify({
        gender: document.getElementById("gender").value,
        age: parseInt(document.getElementById("age").value, 10),
        climate: document.getElementById("climate").value,
      }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Something went wrong");
    }

    // Hide the form, start quiz
    startQuizPhase();
  } catch (err) {
    errEl.textContent = err.message;
    btn.disabled = false;
    btn.textContent = "Continue";
  }
});

// ── Phase 2: Image quiz ───────────────────────────────────────

let quizTree = {};       // { start: "root_m", nodes: { ... } }
let currentNodeId = null;
let questionNumber = 0;
let quizAnswers = [];
let selectedOption = null;

async function startQuizPhase() {
  document.getElementById("quiz-overlay").classList.add("active");

  try {
    const res = await authFetch("/api/quiz/onboarding");
    quizTree = await res.json();
    currentNodeId = quizTree.start;
    questionNumber = 0;
    renderQuestion();
  } catch (err) {
    // Fallback: skip quiz, go to chat
    await finishQuiz();
  }
}

function renderQuestion() {
  const q = quizTree.nodes[currentNodeId];
  if (!q) {
    finishQuiz();
    return;
  }

  questionNumber++;
  document.getElementById("quiz-progress").textContent = `Question ${questionNumber}`;
  document.getElementById("quiz-prompt").textContent = q.prompt;

  const grid = document.getElementById("quiz-grid");
  grid.innerHTML = "";
  selectedOption = null;
  document.getElementById("quiz-next-btn").disabled = true;

  for (const opt of q.options) {
    const card = document.createElement("div");
    card.className = "quiz-card";
    card.dataset.id = opt.id;

    const img = document.createElement("img");
    img.src = opt.image_url;
    img.alt = opt.label;
    img.loading = "lazy";
    card.appendChild(img);

    const label = document.createElement("div");
    label.className = "quiz-label";
    label.textContent = opt.label;
    card.appendChild(label);

    card.addEventListener("click", () => selectCard(card, opt));
    grid.appendChild(card);
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function selectCard(card, option) {
  document.querySelectorAll(".quiz-card.selected").forEach((c) => c.classList.remove("selected"));
  card.classList.add("selected");
  selectedOption = option;
  document.getElementById("quiz-next-btn").disabled = false;
}

document.getElementById("quiz-next-btn").addEventListener("click", async () => {
  if (!selectedOption) return;

  quizAnswers.push({
    category: currentNodeId,
    choice: selectedOption.id,
    style_tags: selectedOption.style_tags,
  });

  const nextNodeId = selectedOption.next;

  if (nextNodeId && quizTree.nodes[nextNodeId]) {
    currentNodeId = nextNodeId;
    renderQuestion();
  } else {
    await finishQuiz();
  }
});

async function finishQuiz() {
  const btn = document.getElementById("quiz-next-btn");
  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    if (quizAnswers.length > 0) {
      await authFetch("/api/profile/style-quiz", {
        method: "POST",
        body: JSON.stringify({ answers: quizAnswers }),
      });
    }
  } catch {}

  location.replace("/chat.html");
}
