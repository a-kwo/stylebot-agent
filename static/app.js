// Redirect to login if not authenticated
const token = localStorage.getItem("stylebot_token");
if (!token) location.replace("/");

const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send-btn");

// Authenticated fetch helper
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

// ── DOM helpers ────────────────────────────────────────────────

function addUserMessage(text) {
  const wrap = document.createElement("div");
  wrap.className = "message user";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  scrollBottom();
}

function addThinkingIndicator() {
  const wrap = document.createElement("div");
  wrap.className = "message assistant";
  wrap.id = "thinking-wrap";
  const bubble = document.createElement("div");
  bubble.className = "thinking-bubble";
  bubble.textContent = "StyleBot is thinking";
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  scrollBottom();
}

function removeThinkingIndicator() {
  const el = document.getElementById("thinking-wrap");
  if (el) el.remove();
}

function renderResponseBlocks(blocks) {
  for (const block of blocks) {
    if (block.type === "text" && block.content) {
      const wrap = document.createElement("div");
      wrap.className = "message assistant";
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = block.content;
      wrap.appendChild(bubble);
      messagesEl.appendChild(wrap);
    } else if (block.type === "products" && block.items?.length) {
      messagesEl.appendChild(buildProductsBlock(block.items));
    }
  }
  scrollBottom();
}

function buildProductsBlock(items) {
  const wrap = document.createElement("div");
  wrap.className = "message assistant";

  const container = document.createElement("div");
  container.className = "products-block";
  container.style.maxWidth = "100%";

  const label = document.createElement("div");
  label.className = "block-label";
  label.textContent = `${items.length} result${items.length !== 1 ? "s" : ""} from Google Shopping`;
  container.appendChild(label);

  const grid = document.createElement("div");
  grid.className = "products-grid";

  for (const item of items) {
    grid.appendChild(buildProductCard(item));
  }

  container.appendChild(grid);
  wrap.appendChild(container);
  return wrap;
}

function buildProductCard(item) {
  const card = document.createElement("div");
  card.className = "product-card";

  if (item.image_url) {
    const img = document.createElement("img");
    img.src = item.image_url;
    img.alt = item.title;
    img.loading = "lazy";
    card.appendChild(img);
  } else {
    const placeholder = document.createElement("div");
    placeholder.style.cssText = "width:100%;aspect-ratio:1;background:#f0f0f0;display:flex;align-items:center;justify-content:center;font-size:2rem;";
    placeholder.textContent = "👗";
    card.appendChild(placeholder);
  }

  const body = document.createElement("div");
  body.className = "card-body";

  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = item.title;
  body.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "card-meta";

  if (item.price) {
    const price = document.createElement("span");
    price.className = "card-price";
    price.textContent = `$${parseFloat(item.price).toFixed(2)}`;
    meta.appendChild(price);
  }

  if (item.seller) {
    const seller = document.createElement("span");
    seller.className = "card-condition";
    seller.textContent = item.seller;
    meta.appendChild(seller);
  }

  body.appendChild(meta);

  if (item.item_url) {
    const link = document.createElement("a");
    link.className = "card-buy";
    link.href = item.item_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "View Product ↗";
    body.appendChild(link);
  }

  card.appendChild(body);
  return card;
}

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ── Load conversation history on page load ─────────────────

async function loadHistory() {
  try {
    const res = await authFetch("/conversations");
    if (!res.ok) return;
    const history = await res.json();

    // Clear default greeting if there's saved history
    const savedTurns = history.filter(m => m.role === "user" || m.role === "assistant");
    if (savedTurns.length === 0) return;

    messagesEl.innerHTML = "";

    for (const msg of history) {
      if (msg.role === "user") {
        // User messages: content may be a plain string or a tool_result array — skip tool results
        if (typeof msg.content === "string") {
          addUserMessage(msg.content);
        }
      } else if (msg.role === "assistant") {
        // Assistant messages: content is an array of blocks
        const blocks = Array.isArray(msg.content) ? msg.content : [];
        const textBlocks = blocks
          .filter(b => b.type === "text" && b.text)
          .map(b => ({ type: "text", content: b.text }));
        if (textBlocks.length > 0) renderResponseBlocks(textBlocks);
      }
    }
  } catch (err) {
    // Non-critical — silently continue
  }
}

loadHistory();

// ── Logout ─────────────────────────────────────────────────

document.getElementById("logout-btn").addEventListener("click", () => {
  localStorage.removeItem("stylebot_token");
  location.replace("/");
});

// ── Auto-grow textarea ──────────────────────────────────────

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

// ── Send message ────────────────────────────────────────────

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;

  addUserMessage(text);
  addThinkingIndicator();

  try {
    const res = await authFetch("/chat", {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });

    removeThinkingIndicator();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderResponseBlocks(data.blocks || []);
  } catch (err) {
    removeThinkingIndicator();
    const wrap = document.createElement("div");
    wrap.className = "message assistant";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.style.color = "#c00";
    bubble.textContent = err.message || "Something went wrong. Please try again.";
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    scrollBottom();
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
});
