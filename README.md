# Music Soulmate Finder 💚

A small web app that lets people track their music taste and find "music soulmates" with similar listening profiles.

## Current Status (Week 1, Day 1)

- ✅ Project folder created
- ✅ Python virtual environment set up
- ✅ Flask backend initialized
- ✅ Basic `/health` endpoint returns JSON

## Tech Stack (Planned)

- Backend: Python (Flask)
- Database: Supabase or PostgreSQL (via Supabase)
- Frontend: React (later weeks)
- Hosting: Vercel (frontend) + Render/Railway (backend)

## How to Run the Backend (Dev)

1. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   # or
   venv\Scripts\activate     # Windows

## Cloud-Ready Design (AWS, Free Tier Friendly)

- Flask + Spotify API locally, API-first design.
- Ready for API Gateway → Lambda → DynamoDB.
- Core aggregation logic in `backend/taste_profile.py` so it can be reused directly in Lambda.
- `backend/save_taste_profile_locally.py` generates DynamoDB-style records (pk/sk).
- Frontend planned for S3 (+ optional CloudFront).

## Week 1 Progress – Local Dev + AWS-Ready Design

- Connected to the Spotify Web API (`backend/spotify_client.py`)
- Added JSON endpoints:
  - GET /health
  - GET /me
  - GET /top-artists
  - GET /top-tracks
  - GET /taste-profile
- Built reusable taste profile logic (`backend/taste_profile.py`)
- Simulated DynamoDB pk/sk design by saving records to data/taste_profile_<user>.json
- Added AWS architecture doc (API Gateway → Lambda → DynamoDB → S3/CloudFront)
- Built a dev dashboard UI (`backend/templates/index.html` + `backend/static/app.js`)
