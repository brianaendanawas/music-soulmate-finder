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

## Week 2 – AWS Lambda (Taste Profile)

### Day 3
- Packaged Lambda code into `lambda_package.zip`
- Deployed `music-soulmate-taste-profile` Lambda (Python 3.12)
- Tested with sample event
- Verified CloudWatch logs
- Added custom metric filter:
  - Namespace: MusicSoulmate
  - Metric: TasteProfileInvocations
  - Pattern: "TasteProfile invocation received"

### Day 4 – API Gateway HTTP API

- Added POST /taste-profile route integrated with Lambda.
- Enabled CORS.
- Tested the endpoint using HTTP POST from local machine.
- Lambda now supports API Gateway proxy event format.

### Day 5 – Frontend calling AWS API

- Updated `backend/static/app.js` to call the AWS HTTP API Gateway endpoint
  (`POST https://7rn3olmit4.execute-api.us-east-1.amazonaws.com/taste-profile`)
  instead of a local Flask `/taste-profile` route.
- Added loading, success, and error states for the Taste Profile panel.
- The local dashboard now talks directly to AWS Lambda via API Gateway.


## Week 2 – First Lambda + API Gateway

Goal: Move the “taste profile” logic into AWS so the app looks and behaves like a real cloud project.

### Day 1 – Extract taste profile logic
- Moved the core taste profile builder into `lambda/build_taste_profile.py`.

### Day 2 – Lambda handler + local testing
- Added `lambda/handler.py`.
- Created local test script.

### Day 3 – Deploy Lambda + CloudWatch metrics
- Deployed Lambda.
- Added CloudWatch Logs metric filter (TasteProfileInvocations).

### Day 4 – HTTP API Gateway
- Created **HTTP API**.
- Connected POST /taste-profile to Lambda.
- Enabled CORS.

### Day 5 – Frontend calling AWS
- Updated `app.js` to call API Gateway.
- Added loading/error states.

### Day 6 – Architecture docs
- Added `docs/week2/aws-lambda-architecture.md`
- Added `docs/week2/api-gateway-design.md`
- Updated README to tell a clear cloud-engineering story.

### AWS Proof (Week 2)
Screenshots: `docs/week2/screenshots/`
- Lambda test success output
- CloudWatch Logs for invocation
- API Gateway POST /taste-profile response

### Week 3 – Persist Taste Profiles (DynamoDB)

- Lambda builds and persists music taste profiles
- Profiles are overwritten by `user_id`
- CloudWatch logs confirm successful saves

**Proof**

![DynamoDB](docs/week3/screenshots/week3-03-dynamodb-profiles.png)  
![Lambda Matches](docs/week3/screenshots/week3-05-lambda-matches-success.png)  
![CloudWatch](docs/week3/screenshots/week3-03-cloudwatch-profile-saved.png)

## Week 3: Music Matching + DynamoDB (AWS)

### What’s working
- ✅ POST `/taste-profile` builds and saves taste profiles to DynamoDB
- ✅ GET `/matches/{user_id}?limit=10` returns a ranked list of matches
- ✅ Matching is explainable: scan → score → sort → top N

### Architecture
API Gateway (HTTP API)  
↓  
Lambda (handler.py: save + match routes)  
↓  
DynamoDB (Profiles)

### Docs (Week 3)
- [AWS Architecture](docs/week3/aws-architecture.md)
- [Profile Storage](docs/week3/profile-storage.md)
- [Matching Logic](docs/week3/matching-logic.md)

### Quick test (PowerShell)
```powershell
$BASE = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com"
Invoke-RestMethod "$BASE/matches/briana_test_002"
Invoke-RestMethod "$BASE/matches/briana_test_002?limit=5"
