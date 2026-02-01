// Music Soulmate Finder — Minimal Demo Client (Polished)
// Calls: GET /matches/{user_id}?limit=N
// Plus:  GET /profiles/{user_id}
// Plus:  POST /connect

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

  // Day 3:
  matchList: document.getElementById("matchList"),
  profileMeta: document.getElementById("profileMeta"),
  profileOutput: document.getElementById("profileOutput"),
};

let lastJsonText = "";

// Day 6: local UI state so Connect becomes "Connected ✓" without duplicates
let connectedSet = new Set();
let currentMatches = [];
let currentUserId = "";

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

function setSelectedProfile(metaText, objOrText) {
  // metaText: small line above the profile JSON
  if (els.profileMeta) els.profileMeta.textContent = metaText;

  if (!els.profileOutput) return;

  if (typeof objOrText === "string") {
    els.profileOutput.textContent = objOrText;
    return;
  }
  els.profileOutput.textContent = JSON.stringify(objOrText, null, 2);
}

function clearMatchUI() {
  if (els.matchList) {
    els.matchList.innerHTML = `<div class="muted">Run “Find Matches” to populate this list.</div>`;
  }
  if (els.profileMeta) {
    els.profileMeta.textContent = "Click a match to load their profile…";
  }
  if (els.profileOutput) {
    els.profileOutput.textContent = "// Profile JSON will appear here";
  }
}

function showSummary(matches, forUserId, limit) {
  if (!Array.isArray(matches)) {
    els.summary.classList.add("hidden");
    return;
  }

  const top = matches[0];

  const topArtistCount = top?.shared_artist_count ?? 0;
  const topGenreCount = top?.shared_genre_count ?? 0;

  const percent =
    top && top.match_percent != null ? `${top.match_percent}%` : null;

  const fallbackScore = top?.score ?? 0;

  const topLine = top
    ? `Top match: ${top.display_name || top.user_id} (@${top.user_id}) — ${topArtistCount} shared artists — ${topGenreCount} shared genres — Match ${
        percent ?? `${fallbackScore}%`
      }`
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

function buildMatchesUrl(userId, limit) {
  const encodedUserId = encodeURIComponent(userId.trim());
  const encodedLimit = encodeURIComponent(String(limit));
  return `${API_BASE}/matches/${encodedUserId}?limit=${encodedLimit}`;
}

function buildProfileUrl(userId) {
  const encodedUserId = encodeURIComponent(userId.trim());
  return `${API_BASE}/profiles/${encodedUserId}`;
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
  if (data && typeof data === "object" && Array.isArray(data.matches)) {
    return data.matches;
  }
  return Array.isArray(data) ? data : [];
}

// -------------------------
// Connect
// -------------------------
async function connectUser(fromUserId, toUserId) {
  const url = `${API_BASE}/connect`;

  // Prevent self-connect + duplicates (UI + logic)
  if (fromUserId === toUserId) {
    showError("You can’t connect to yourself 🙂");
    return false;
  }
  if (connectedSet.has(toUserId)) {
    setStatus("ok", "Already connected ✓");
    return true;
  }

  // light feedback
  if (els.profileMeta) {
    els.profileMeta.textContent = `Connecting ${fromUserId} → ${toUserId}…`;
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        from_user_id: fromUserId,
        to_user_id: toUserId,
      }),
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }

    if (!res.ok) {
      showError(`Connect failed (HTTP ${res.status}).`);
      if (els.profileMeta) els.profileMeta.textContent = "Connect failed";
      if (els.profileOutput) {
        els.profileOutput.textContent =
          typeof data === "string" ? data : JSON.stringify(data, null, 2);
      }
      return false;
    }

    console.log("Connect success:", data);
    if (els.profileMeta) {
      els.profileMeta.textContent = `Connected ✅ (${fromUserId} → ${toUserId})`;
    }
    if (els.profileOutput) {
      els.profileOutput.textContent =
        typeof data === "string" ? data : JSON.stringify(data, null, 2);
    }

    // Day 6: update local UI state and re-render list to show "Connected ✓"
    connectedSet.add(toUserId);
    renderMatchList(currentMatches);

    setStatus("ok", "Connected ✓", `${fromUserId} → ${toUserId}`);
    return true;
  } catch (err) {
    showError(
      "Network error connecting. If PowerShell works but browser fails, it’s usually CORS."
    );
    if (els.profileMeta) els.profileMeta.textContent = "Network error connecting";
    return false;
  }
}

function renderMatchList(matches) {
  if (!els.matchList) return;

  currentMatches = Array.isArray(matches) ? matches : [];
  currentUserId = els.userId.value.trim();

  if (!Array.isArray(matches) || matches.length === 0) {
    els.matchList.innerHTML = `<div class="muted">No matches to display.</div>`;
    return;
  }

  els.matchList.innerHTML = matches
    .map((m) => {
      const name = escapeHtml(m.display_name || m.user_id);
      const uid = escapeHtml(m.user_id);

      const sharedArtists = escapeHtml(String(m.shared_artist_count ?? 0));
      const sharedGenres = escapeHtml(String(m.shared_genre_count ?? 0));

      const matchPercent =
        m.match_percent != null ? escapeHtml(String(m.match_percent)) : null;

      const fallbackScore = escapeHtml(String(m.score ?? 0));

      const isSelf = currentUserId && uid === escapeHtml(currentUserId);
      const isConnected = connectedSet.has(m.user_id);

      const connectLabel = isConnected ? "Connected ✓" : "Connect";
      const disabledAttr = isSelf || isConnected ? "disabled" : "";

      const matchLabel = matchPercent != null ? `Match ${matchPercent}%` : `Score ${fallbackScore}`;

      return `
        <div class="match-row">
          <button class="match-item" type="button" data-user-id="${uid}">
            <div class="match-title">${name} <span class="muted">(@${uid})</span></div>
            <div class="match-sub muted">${sharedArtists} shared artists • ${sharedGenres} shared genres • ${matchLabel}</div>
          </button>

          <button class="connect-btn" type="button" data-target-user-id="${uid}" ${disabledAttr}>
            ${connectLabel}
          </button>
        </div>
      `;
    })
    .join("");

  // click handlers for loading profile
  els.matchList.querySelectorAll(".match-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const uid = btn.getAttribute("data-user-id");
      if (uid) fetchProfile(uid);
    });
  });

  // click handlers for connect
  els.matchList.querySelectorAll(".connect-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();

      const targetId = btn.getAttribute("data-target-user-id");
      const fromId = els.userId.value.trim();

      if (!fromId) {
        showError("Enter your user_id first (the left input), then click Connect.");
        return;
      }
      if (!targetId) return;

      await connectUser(fromId, targetId);
    });
  });
}

async function fetchProfile(userId) {
  const url = buildProfileUrl(userId);

  setSelectedProfile(`Loading profile: ${url}`, `Requesting:\n${url}\n\n…`);

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
      const msg =
        typeof data === "string"
          ? data
          : data?.message || data?.error || "Request failed";

      setSelectedProfile(
        `Error (HTTP ${res.status}) loading profile`,
        typeof data === "string" ? data : data
      );

      showError(
        `Profile request failed (HTTP ${res.status}). ${msg} ${
          res.status === 404 ? "Check user_id exists in DynamoDB." : ""
        }`
      );
      return;
    }

    setSelectedProfile(`Loaded profile for ${userId}`, data);
    setStatus("ok", "Profile loaded", userId);
  } catch (err) {
    setSelectedProfile(
      "Network error loading profile",
      err?.message || String(err)
    );
    showError(
      "Network error loading profile. If PowerShell works but the browser fails, it’s usually CORS."
    );
  }
}

async function fetchMatches() {
  clearError();

  const userId = els.userId.value.trim();
  const limit = Number(els.limit.value || 10);

  // Day 6: reset local connected state per “session run”
  connectedSet = new Set();
  currentMatches = [];
  currentUserId = userId;

  if (!userId) {
    setStatus("error", "Missing user_id");
    showError("Please enter a user_id (example: briana_test_002).");
    setOutput("// Results will appear here");
    els.summary.classList.add("hidden");
    clearMatchUI();
    return;
  }

  const url = buildMatchesUrl(userId, limit);

  els.btnFind.disabled = true;
  setStatus("loading", "Loading…", url);
  els.summary.classList.add("hidden");
  setOutput(`Requesting:\n${url}\n\n…`);

  // reset panels for a new run
  if (els.profileMeta)
    els.profileMeta.textContent = "Click a match to load their profile…";
  if (els.profileOutput)
    els.profileOutput.textContent = "// Profile JSON will appear here";
  if (els.matchList)
    els.matchList.innerHTML = `<div class="muted">Loading matches…</div>`;

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
          "If this works in PowerShell but fails in the browser, it's usually CORS. Enable CORS in API Gateway for GET/POST/OPTIONS.",
      });

      clearMatchUI();
      return;
    }

    const cleanedMatches = normalizeMatchesResponse(data);

    setStatus("ok", "Success", url);

    // render clickable matches list (includes Connect + Connected state)
    renderMatchList(cleanedMatches);

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
      tip: "If this works in PowerShell but not in the browser, enable CORS in API Gateway.",
    });

    clearMatchUI();
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
  clearMatchUI();
}

function clearAll() {
  els.userId.value = "";
  els.limit.value = "10";
  clearError();
  setStatus("idle", "Idle");
  els.summary.classList.add("hidden");
  setOutput("// Results will appear here");

  // Day 6: clear local state too
  connectedSet = new Set();
  currentMatches = [];
  currentUserId = "";

  clearMatchUI();
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
