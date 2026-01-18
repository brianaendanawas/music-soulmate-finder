// Music Soulmate Finder — Minimal Demo Client (Polished)
// Calls: GET /matches/{user_id}?limit=N

const API_BASE = "https://7rn3olmit4.execute-api.us-east-1.amazonaws.com";

const els = {
  form: document.getElementById("form"),
  userId: document.getElementById("userId"),
  limit: document.getElementById("limit"),
  btnFind: document.getElementById("btnFind"),
  btnSample: document.getElementById("btnSample"),
  btnClear: document.getElementById("btnClear"),
  btnCopy: document.getElementById("btnCopy"),
  output: document.getElementById("output"),
  summary: document.getElementById("summary"),
  errorBox: document.getElementById("errorBox"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  statusMeta: document.getElementById("statusMeta"),
};

let lastJsonText = "";

function setStatus(state, text, meta = "") {
  els.statusDot.className = `dot ${state}`;
  els.statusText.textContent = text;
  els.statusMeta.textContent = meta;
}

function showError(message) {
  els.errorBox.textContent = message;
  els.errorBox.classList.remove("hidden");
}

function clearError() {
  els.errorBox.textContent = "";
  els.errorBox.classList.add("hidden");
}

function setOutput(obj) {
  if (typeof obj === "string") {
    els.output.textContent = obj;
    lastJsonText = "";
    els.btnCopy.disabled = true;
    return;
  }

  const pretty = JSON.stringify(obj, null, 2);
  els.output.textContent = pretty;
  lastJsonText = pretty;
  els.btnCopy.disabled = false;
}

function showSummary(matches, forUserId, limit) {
  if (!Array.isArray(matches)) {
    els.summary.classList.add("hidden");
    return;
  }

  const top = matches[0];

  const topLine = top
    ? `Top match: ${top.display_name || top.user_id} (@${top.user_id}) — ${top.shared_artist_count ?? 0} shared artists — score: ${top.score}`
    : "No matches returned.";

  els.summary.innerHTML = `
    <strong>For:</strong> ${escapeHtml(forUserId)}
    &nbsp; • &nbsp;
    <strong>Limit:</strong> ${escapeHtml(String(limit))}
    <br/>
    ${escapeHtml(topLine)}
  `;
  els.summary.classList.remove("hidden");
}

function buildUrl(userId, limit) {
  const encodedUserId = encodeURIComponent(userId.trim());
  const encodedLimit = encodeURIComponent(String(limit));
  return `${API_BASE}/matches/${encodedUserId}?limit=${encodedLimit}`;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeMatchesResponse(data) {
  // Your API returns: { for_user_id, limit, matches: [...] }
  // Support both shapes safely.
  if (data && typeof data === "object" && Array.isArray(data.matches)) {
    return data.matches;
  }
  return Array.isArray(data) ? data : [];
}

async function fetchMatches() {
  clearError();

  const userId = els.userId.value.trim();
  const limit = Number(els.limit.value || 10);

  if (!userId) {
    setStatus("error", "Missing user_id");
    showError("Please enter a user_id (example: briana_test_002).");
    setOutput("// Results will appear here");
    els.summary.classList.add("hidden");
    return;
  }

  const url = buildUrl(userId, limit);

  els.btnFind.disabled = true;
  setStatus("loading", "Loading…", url);
  els.summary.classList.add("hidden");
  setOutput(`Requesting:\n${url}\n\n…`);

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }

    if (!res.ok) {
      setStatus("error", `HTTP ${res.status}`, url);

      const msg =
        typeof data === "string"
          ? data
          : data?.message || data?.error || "Request failed";

      showError(
        `Request failed (HTTP ${res.status}). ${msg} ${
          res.status === 404 ? "Check user_id exists in DynamoDB." : ""
        }`
      );

      setOutput({
        error: "Request failed",
        status: res.status,
        response: data,
        tip:
          "If this works in PowerShell but fails in the browser, it's usually CORS. Enable CORS in API Gateway for GET/OPTIONS.",
      });
      return;
    }

    // Create a cleaned view for summary
    const cleanedMatches = normalizeMatchesResponse(data);

    setStatus("ok", "Success", url);

    // If we filtered matches, preserve your original response shape but replace matches list
    if (data && typeof data === "object" && "matches" in data) {
      const patched = { ...data, matches: cleanedMatches };
      showSummary(cleanedMatches, userId, limit);
      setOutput(patched);
    } else {
      showSummary(cleanedMatches, userId, limit);
      setOutput(data);
    }
  } catch (err) {
    setStatus("error", "Network error", url);
    showError(
      "Network error. If PowerShell works but the browser fails, it’s almost always CORS."
    );
    setOutput({
      error: "Network error",
      message: err?.message || String(err),
      tip:
        "If this works in PowerShell but not in the browser, enable CORS in API Gateway.",
    });
  } finally {
    els.btnFind.disabled = false;
  }
}

function loadSample() {
  els.userId.value = "briana_test_002";
  els.limit.value = "10";
  clearError();
  setStatus("idle", "Sample loaded");
  els.summary.classList.add("hidden");
  setOutput("// Click “Find Matches” to run the demo.");
}

function clearAll() {
  els.userId.value = "";
  els.limit.value = "10";
  clearError();
  setStatus("idle", "Idle");
  els.summary.classList.add("hidden");
  setOutput("// Results will appear here");
}

async function copyJson() {
  if (!lastJsonText) return;
  try {
    await navigator.clipboard.writeText(lastJsonText);
    setStatus("ok", "Copied JSON ✅", els.statusMeta.textContent);
    setTimeout(() => setStatus("ok", "Success", els.statusMeta.textContent), 900);
  } catch {
    showError("Could not copy to clipboard (browser permission).");
  }
}

// Submit on Enter
els.form.addEventListener("submit", (e) => {
  e.preventDefault();
  fetchMatches();
});

els.btnSample.addEventListener("click", loadSample);
els.btnClear.addEventListener("click", clearAll);
els.btnCopy.addEventListener("click", copyJson);

// Initialize
clearAll();
