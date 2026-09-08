const questionInput = document.getElementById("question");
const askBtn = document.getElementById("ask-btn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const badgeEl = document.getElementById("badge");
const answerEl = document.getElementById("answer");
const confidenceEl = document.getElementById("confidence");
const citationListEl = document.getElementById("citation-list");

const BADGE_LABEL = {
  answered: "Answered",
  not_covered: "Not covered by the rulebook",
  conflict: "Conflict between sections",
};

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    questionInput.value = chip.dataset.q;
    ask();
  });
});

askBtn.addEventListener("click", ask);
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") ask();
});

async function ask() {
  const question = questionInput.value.trim();
  if (question.length < 3) {
    statusEl.innerHTML = '<div class="error">Type a full question first.</div>';
    return;
  }

  askBtn.disabled = true;
  resultEl.classList.remove("visible");
  statusEl.innerHTML = '<div class="loading">Searching the rulebook…</div>';

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ? JSON.stringify(body.detail) : `HTTP ${res.status}`);
    }
    const data = await res.json();
    render(data);
    statusEl.innerHTML = "";
  } catch (err) {
    statusEl.innerHTML = `<div class="error">Something went wrong: ${escapeHtml(err.message)}</div>`;
  } finally {
    askBtn.disabled = false;
  }
}

function render(data) {
  badgeEl.textContent = BADGE_LABEL[data.type] || data.type;
  badgeEl.className = `badge ${data.type}`;
  answerEl.textContent = data.answer;

  confidenceEl.textContent = data.confidence ? `Confidence: ${data.confidence}` : "";

  citationListEl.innerHTML = "";
  data.citations.forEach((c) => {
    const div = document.createElement("div");
    div.className = "citation" + (data.type === "conflict" ? " conflict-side" : "");
    const pct = Math.max(0, Math.min(100, Math.round(c.score * 100)));
    div.innerHTML = `
      <div class="citation-head">
        <span class="ref">${escapeHtml(c.section_id)} — ${escapeHtml(c.title)}</span>
        <span class="source">${escapeHtml(c.source_file)}</span>
      </div>
      <div class="score-row">
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${pct}%"></div></div>
        <span class="score-value">similarity ${c.score.toFixed(3)}</span>
      </div>
      <div class="citation-text">${escapeHtml(c.text)}</div>
    `;
    citationListEl.appendChild(div);
  });

  resultEl.classList.add("visible");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
