# Week 5 Architecture (Current)

This diagram reflects the current “social foundation” version of Music Soulmate Finder:
profiles + matches + public profile view + connections.

---

## High-level system

```text
User (browser)
  |
  | 1. GET /matches/{user_id}?limit=N
  | 2. GET /profiles/{user_id}
  | 3. POST /connect
  v
API Gateway (HTTP API)
  |
  v
AWS Lambda (Python)
  |
  v
DynamoDB: music-soulmate-profiles
  - PK: user_id
  - Item contains:
      profile (map)
      display_name, bio
      top_artists_preview (list)
      connections (list)
      updated_at
```

## Request flows
### A. Find matches
1. User enters `user_id` in demo UI
2. UI calls `GET /matches/{user_id}?limit=N`
3. Lambda:
  - `GetItem` for the user
  - `Scan` other users
  - computes match score & shared lists
4. Response: list of matches

### B. View profile
1. User clicks a match row
2. UI calls `GET /profiles/{user_id}`
3. Lambda: `GetItem` and returns public profile shape

### C. Connect
1. User clicks “Connect”
2. UI calls `POST /connect` with `{from_user_id, to_user_id}`
3. Lambda:
  - `GetItem` both users (validate exists)
  - `UpdateItem` on from-user to append to_user_id into connections
4. Response: updated connections list

## Notes
- Spotify OAuth is paused to keep the project scope focused and serverless-first.
- The match scoring logic is a known issue (scores currently show 0).