// Music Soulmate Finder — Minimal Demo Client
// Calls: GET /matches/{user_id}?limit=N

const API_BASE = "https://7rn3olmit4.execute-api.us-east-1.amazonaws.com";

const els = {
  userId: document.getElementById("userId"),
  limit: document.getElementById("limit"),
  btnFind: document.getElementById("btnFind"),
  btnSample: document.getElementById("btnSample"),
  output: document.getElementById("output"),
  summary: document.getElementById("summary"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
};

function setStatus(state, text) {
  els.statusDot.className = `dot ${state}`;
  els.statusText.textContent = text;
}

function setOutput(obj) {
  els.output.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
}

function showSummary(matches, forUserId, limit) {
  if (!Array.isArray(matches)) {
    els.summary.classList.add("hidden");
    return;
  }

  const top = matches[0];
  const topLine = top
    ? `Top match: ${top.user_id} (score: ${top.score})`
    : "No matches returned.";

  els.summary.innerHTML = `
    <strong>For:</strong> ${forUserId}
    &nbsp; • &nbsp;
    <strong>Limit:</strong> ${limit}
    <br/>
    ${topLine}
  `;
  els.summary.classList.remove("hidden");
}

function buildUrl(userId, limit) {
  const encodedUserId = encodeURIComponent(userId.trim());
  const encodedLimit = encodeURIComponent(String(limit));
  return `${API_BASE}/matches/${encodedUserId}?limit=${encodedLimit}`;
}

async function fetchMatches() {
  const userId = els.userId.value.trim();
  const limit = Number(els.limit.value || 10);

  if (!userId) {
    setStatus("error", "Missing user_id");
    setOutput("Please enter a user_id (example: briana_test_002).");
    return;
  }

  const url = buildUrl(userId, limit);

  els.btnFind.disabled = true;
  setStatus("loading", "Loading…");
  els.summary.classList.add("hidden");
  setOutput(`Requesting:\n${url}\n\n…`);

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }

    if (!res.ok) {
      setStatus("error", `HTTP ${res.status}`);
      setOutput({
        error: "Request failed",
        status: res.status,
        response: data,
        tip:
          "If this is a CORS error in the browser console, enable CORS for this route in API Gateway.",
      });
      return;
    }

    // Your Lambda returns an object like: { for_user_id, limit, matches: [...] }
    const matches = data && data.matches ? data.matches : data;

    setStatus("ok", "Success");
    showSummary(matches, userId, limit);
    setOutput(data);
  } catch (err) {
    setStatus("error", "Network error");
    setOutput({
      error: "Network error",
      message: err?.message || String(err),
      tip:
        "If this works in PowerShell but not in the browser, it is almost always CORS.",
    });
  } finally {
    els.btnFind.disabled = false;
  }
}

els.btnFind.addEventListener("click", fetchMatches);

els.btnSample.addEventListener("click", () => {
  els.userId.value = "briana_test_002";
  els.limit.value = "10";
  setStatus("idle", "Sample loaded");
  setOutput("// Click “Find Matches” to run the demo.");
});
