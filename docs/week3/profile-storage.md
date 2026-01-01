# Week 3 — Profile Storage Design (DynamoDB)

## Goal
Persist each user's computed "taste profile" so we can:
- fetch it later
- compare it to other users
- return match results

## DynamoDB Table (planned)
**Table name:** music-soulmate-profiles  
**Partition key (PK):** user_id (String)  
**Billing:** On-demand (PAY_PER_REQUEST)

### Why this model?
- Simple: one item per user
- Cheap/free-tier friendly
- Easy to query by user_id
- Easy to scan for matching (temporary approach)

## Item shape (stored fields)
### Required
- `user_id` (String) — unique id for the user (from frontend)
- `created_at` (String, ISO timestamp)
- `updated_at` (String, ISO timestamp)
- `favorite_artists` (List[String]) — top artists (deduped)
- `top_genres` (List[String]) — derived genres (deduped)
- `top_tracks` (List[String]) — optional but helpful for match scoring

### Stats (Map)
- `artist_count` (Number)
- `genre_variety` (Number)
- `track_count` (Number)

## API flow
### POST /taste-profile
1. Frontend sends a `user_id` + raw Spotify data (artists/tracks lists)
2. Lambda computes taste profile (already have this)
3. Lambda writes the profile to DynamoDB using `user_id`
4. Lambda returns the profile (and later: maybe a "saved": true flag)

### GET /matches/{user_id} (later this week)
1. Lambda loads the requesting user's profile via `GetItem(user_id)`
2. Lambda scans other profiles (temporary) using `Scan`
3. Lambda computes a similarity score for each
4. Returns top 5–10 matches

## Notes / future upgrades (not now)
- Add sort key for versions (user_id + profile_version)
- Use a GSI for genre-based lookups instead of Scan
- Store hidden artists/tracks (stretch goal) per user
