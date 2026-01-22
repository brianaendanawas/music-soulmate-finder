# Music Soulmate Finder (MSF)

A lightweight, serverless “music soulmate” backend + demo UI.  
Users create a music taste profile, fetch ranked matches, view public profiles, and **connect** with others (social foundation).

This project intentionally avoids heavy auth / messaging / complex pipelines right now — it focuses on clear backend logic + real AWS infrastructure.

---

## What it does today

### Core API (AWS)
- **POST `/taste-profile`**  
  Save a user’s taste profile into DynamoDB (plus display name + bio).
- **GET `/matches/{user_id}?limit=N`**  
  Scan other profiles and compute match results (score + shared artists/genres/tracks).
- **GET `/profiles/{user_id}`**  
  View a user’s public profile JSON.
- **POST `/connect`** ✅ (Week 5 Day 4)  
  “User A connects to User B” — stored on User A’s item as a `connections` list.

### Demo UI (simple)
- Enter a `user_id` → fetch matches list
- Click a match → view profile JSON
- Click **Connect** → sends POST `/connect` and shows response JSON

---

## Why Spotify OAuth is paused (for now)

Week 1 used real Spotify OAuth to build profiles from a real account — it was cool, but it also introduced:
- auth complexity
- token refresh + storage
- more moving parts than needed for the current goal

**Current goal:** build a clean “social backend foundation” first (profiles, matches, connections).  
Spotify OAuth can come back later as a stretch feature once the core app behavior is strong.

Planned return:
- add short/medium/long-term toggle for Spotify top artists/tracks
- allow users to hide artists/songs (front-end localStorage first, optional DynamoDB later)

---

## Architecture (current)

**Backend**
- API Gateway (HTTP API)
- AWS Lambda (Python)
- DynamoDB table: `music-soulmate-profiles`

**Data model (single-table style)**
Each user is stored as one DynamoDB item:
- `user_id` (partition key)
- `profile` (taste profile map)
- `display_name`, `bio`
- `top_artists_preview` (small list for UI)
- `connections` (list of user_ids)
- `updated_at`

---

## Social roadmap (where this is going)

This project is evolving from “matching demo” → “early social app foundation”.

Next steps (in small, realistic increments):
1. **Fix match scoring bug** (currently scores display as 0)  
2. Connection UI improvements:
   - show “Connected” state per match
   - prevent duplicate connects in the UI
3. “Connections view” endpoint:
   - GET `/connections/{user_id}` → list connected users (public profile summaries)
4. Later (optional):
   - messaging (very minimal)
   - auth (Cognito) if needed
   - Spotify OAuth re-integration

---

## Known issues

- **Match score is currently always 0** in the demo output.  
  This is tracked as a fix task (scoring logic debugging) and will be addressed in an upcoming session.

---

## Screenshots (proof it works)

See: `docs/week5/screenshots/`

Recommended captures:
- Matches list + profile view
- Connect action + JSON response
- DynamoDB item showing `connections`

---

## Repo structure (quick map)

- `lambda/` — AWS Lambda backend (handler, matching, helpers)
- `demo/` — simple HTML/JS demo client
- `docs/` — weekly documentation, screenshots, and notes

---

## Local demo (UI)

Open:
- `demo/index.html`

Update `demo/app.js` if you change the API base URL.

---

## API examples

### POST /connect
```json
{
  "from_user_id": "briana_test_003",
  "to_user_id": "briana_test_002"
}
{
  "message": "Connected",
  "from_user_id": "briana_test_003",
  "to_user_id": "briana_test_002",
  "connections": ["briana_test_002"],
  "updated_at": "..."
}
```

## Notes
This project is built to show:
- serverless API design (Lambda + API Gateway)
- structured data modeling in DynamoDB
- debugging with CloudWatch logs + IAM permissions
- incremental delivery (features added week-by-week)
If you want to see the evolution, check docs/week2/, docs/week3/, docs/week4/, docs/week5/.