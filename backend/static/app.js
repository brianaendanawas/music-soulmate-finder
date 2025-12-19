// backend/static/app.js

// Flask base URL for local routes (leave empty for same origin)
const API_BASE_URL = "";

// AWS HTTP API base URL (no trailing slash)
const AWS_API_BASE_URL = "https://7rn3olmit4.execute-api.us-east-1.amazonaws.com";

// Helper to build URLs (used for local Flask endpoints)
function apiUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setHtml(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

async function fetchJson(path) {
  const response = await fetch(apiUrl(path));
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

// --------------------------------------------------
// /me  (local Flask + Spotify)
// --------------------------------------------------
async function loadProfile() {
  setText("profile-status", "Loading profile...");
  try {
    const data = await fetchJson("/me");
    const profile = data.profile;

    if (!profile) {
      setText("profile-status", "No profile data found.");
      return;
    }

    const imageHtml = profile.image_url
      ? `<img src="${profile.image_url}" alt="${profile.display_name}" class="avatar" />`
      : "";

    const followers = profile.followers ?? "N/A";

    const html = `
      ${imageHtml}
      <div class="profile-info">
        <h2>${profile.display_name || "Unknown user"}</h2>
        <p><strong>Spotify ID:</strong> ${profile.id}</p>
        <p><strong>Followers:</strong> ${followers}</p>
        ${
          profile.spotify_url
            ? `<p><a href="${profile.spotify_url}" target="_blank">Open on Spotify</a></p>`
            : ""
        }
      </div>
    `;

    setHtml("profile-card", html);
    setText("profile-status", "");
  } catch (err) {
    console.error(err);
    setText("profile-status", "Error loading profile.");
  }
}

// --------------------------------------------------
// /top-artists  (local Flask + Spotify)
// --------------------------------------------------
async function loadTopArtists() {
  setText("artists-status", "Loading top artists...");
  try {
    const data = await fetchJson("/top-artists");
    const artists = data.top_artists || [];

    if (artists.length === 0) {
      setText("artists-status", "No top artists found.");
      return;
    }

    const listItems = artists
      .map((artist) => {
        const genres = artist.genres?.length
          ? artist.genres.join(", ")
          : "No genres listed";

        const imageHtml = artist.image_url
          ? `<img src="${artist.image_url}" class="thumb" />`
          : "";

        return `
          <li class="artist-item">
            ${imageHtml}
            <div>
              <strong>${artist.name}</strong><br/>
              <small>${genres}</small>
            </div>
          </li>
        `;
      })
      .join("");

    setHtml("artists-list", `<ul class="item-list">${listItems}</ul>`);
    setText("artists-status", "");
  } catch (err) {
    console.error(err);
    setText("artists-status", "Error loading artists.");
  }
}

// --------------------------------------------------
// /top-tracks  (local Flask + Spotify)
// --------------------------------------------------
async function loadTopTracks() {
  setText("tracks-status", "Loading top tracks...");
  try {
    const data = await fetchJson("/top-tracks");
    const tracks = data.top_tracks || [];

    if (tracks.length === 0) {
      setText("tracks-status", "No top tracks found.");
      return;
    }

    const listItems = tracks
      .map((track) => {
        const artists = (track.artists || []).join(", ");
        const spotifyLink = track.spotify_url
          ? `<a href="${track.spotify_url}" target="_blank">Spotify</a>`
          : "";
        const previewLink = track.preview_url
          ? `<a href="${track.preview_url}" target="_blank">Preview</a>`
          : "";

        const links = [spotifyLink, previewLink].filter(Boolean).join(" | ");

        return `
          <li class="track-item">
            <strong>${track.name}</strong><br/>
            <small>${artists}</small><br/>
            ${links ? `<small>${links}</small>` : ""}
          </li>
        `;
      })
      .join("");

    setHtml("tracks-list", `<ul class="item-list">${listItems}</ul>`);
    setText("tracks-status", "");
  } catch (err) {
    console.error(err);
    setText("tracks-status", "Error loading tracks.");
  }
}

// --------------------------------------------------
// Taste Profile → call AWS API Gateway (POST /taste-profile)
// --------------------------------------------------

// Sample request body to send to your Lambda.
// Later we can plug in real Spotify data.
function buildTasteProfileRequestBody() {
  return {
    items: {
      user_id: "spotify:user:briana",
      top_artists: [
        "NCT 127",
        "Lisa",
        "Red Velvet",
        "NewJeans"
      ],
      top_genres: [
        "k-pop",
        "k-pop",
        "r&b",
        "pop"
      ],
      top_tracks: [
        "Favorite – NCT 127",
        "Sticker – NCT 127",
        "No Clue – NCT 127",
        "Chill – Lisa"
      ]
    }
  };
}

async function loadTasteProfile() {
  setText("taste-status", "Loading taste profile from AWS…");
  setHtml("taste-profile", ""); // clear previous

  try {
    const body = buildTasteProfileRequestBody();

    const response = await fetch(`${AWS_API_BASE_URL}/taste-profile`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const text = await response.text();
      console.error("Taste profile error response:", text);
      setText("taste-status", `Error from AWS: HTTP ${response.status}`);
      setHtml("taste-profile", `<pre class="code-block">${text}</pre>`);
      return;
    }

    const data = await response.json();
    console.log("Taste profile from AWS:", data);

    // If Lambda returns { taste_profile: {...} }, prefer that inner object.
    const payload = data.taste_profile || data;

    setText("taste-status", "Taste profile loaded from AWS ✅");

    // Pretty JSON display
    setHtml(
      "taste-profile",
      `<pre class="code-block">${JSON.stringify(payload, null, 2)}</pre>`
    );
  } catch (err) {
    console.error("Taste profile fetch failed:", err);
    setText("taste-status", "Network error calling AWS API. Check console/logs.");
  }
}

// --------------------------------------------------
// Start page
// --------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  loadTopArtists();
  loadTopTracks();
  loadTasteProfile();
});
