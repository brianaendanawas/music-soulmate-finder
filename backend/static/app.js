// backend/static/app.js

// Flask base URL for local routes.
// Leave empty because this frontend is served by the same Flask app.
const API_BASE_URL = "";

// Helper to build local Flask URLs
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

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

// --------------------------------------------------
// Spotify Profile
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

        <p>
          <strong>Spotify ID:</strong>
          ${profile.id}
        </p>

        <p>
          <strong>Followers:</strong>
          ${followers}
        </p>

        ${
          profile.spotify_url
            ? `<p>
                <a href="${profile.spotify_url}" target="_blank">
                  Open on Spotify
                </a>
              </p>`
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
// Top Artists
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

    setHtml(
      "artists-list",
      `<ul class="item-list">${listItems}</ul>`
    );

    setText("artists-status", "");
  } catch (err) {
    console.error(err);
    setText("artists-status", "Error loading artists.");
  }
}

// --------------------------------------------------
// Top Tracks
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

        const links = [spotifyLink, previewLink]
          .filter(Boolean)
          .join(" | ");

        return `
          <li class="track-item">
            <strong>${track.name}</strong><br/>
            <small>${artists}</small><br/>

            ${
              links
                ? `<small>${links}</small>`
                : ""
            }
          </li>
        `;
      })
      .join("");

    setHtml(
      "tracks-list",
      `<ul class="item-list">${listItems}</ul>`
    );

    setText("tracks-status", "");
  } catch (err) {
    console.error(err);
    setText("tracks-status", "Error loading tracks.");
  }
}

// --------------------------------------------------
// Real Spotify Taste Profile
// --------------------------------------------------

async function loadTasteProfile() {
  setText(
    "taste-status",
    "Building taste profile from Spotify..."
  );

  setHtml("taste-profile", "");

  try {
    const data = await fetchJson("/taste-profile");

    const profile = data.taste_profile;

    if (!profile) {
      setText(
        "taste-status",
        "No taste profile found."
      );

      return;
    }

    const genres = (profile.top_genres || [])
      .map((item) => item.genre)
      .filter(Boolean);

    const artists = profile.sample?.top_artists || [];
    const tracks = profile.sample?.top_tracks || [];

    const genresHtml = genres.length
      ? genres.map((genre) => `<li>${genre}</li>`).join("")
      : "<li>No genres found</li>";

    const artistsHtml = artists.length
      ? artists.map((artist) => `<li>${artist}</li>`).join("")
      : "<li>No artists found</li>";

    const tracksHtml = tracks.length
      ? tracks.map((track) => `<li>${track}</li>`).join("")
      : "<li>No tracks found</li>";

    const html = `
      <div>
        <p>
          ${profile.summary?.description || ""}
        </p>

        <h3>Favorite Genres</h3>

        <ul>
          ${genresHtml}
        </ul>

        <h3>Favorite Artists</h3>

        <ul>
          ${artistsHtml}
        </ul>

        <h3>Sample Tracks</h3>

        <ul>
          ${tracksHtml}
        </ul>
      </div>
    `;

    setHtml("taste-profile", html);

    setText(
      "taste-status",
      "Taste profile built from your Spotify listening ✓"
    );
  } catch (err) {
    console.error(err);

    setText(
      "taste-status",
      "Error loading Spotify taste profile."
    );
  }
}

// --------------------------------------------------
// Load dashboard
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  loadTopArtists();
  loadTopTracks();
  loadTasteProfile();
});