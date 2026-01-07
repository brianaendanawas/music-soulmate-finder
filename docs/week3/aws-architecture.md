# Music Soulmate Finder – AWS Architecture (Week 3)

This project starts as a local Flask + Spotify API app, but is designed to be
migrated to a serverless AWS architecture using Free Tier–friendly services.

## High-Level Design

**Goal:** Match users based on their music taste profiles, using Spotify data.

Planned AWS components:

- **Amazon API Gateway (HTTP API)**
  - Public entrypoint for the frontend.
  - Routes:
    - POST /taste-profile
    - GET /matches/{user_id}?limit=10

- **AWS Lambda (Python)**
  - One function for taste profile aggregation.
  - Reuses the same logic found in `backend/taste_profile.py`.
  - Responsible for:
    - Calling Spotify with an access token
    - Building the `taste_profile` object
    - Reading/writing taste profile items in DynamoDB

- **Amazon DynamoDB**

- Stores one item per user taste profile.
- Partition key: `user_id`
- Attributes:
  - `profile` (map)
  - `updated_at` (ISO timestamp)

Each POST to `/taste-profile` overwrites the existing profile for that user.


- **Amazon S3 + (optional) CloudFront**
  - S3: host the frontend (static HTML/JS).
  - CloudFront: global CDN in front of S3 for performance and HTTPS.

- **(Optional later) Amazon Cognito**
  - Manage auth for users beyond Spotify.
  - Issue JWTs that Lambda/API Gateway can validate.

## Free Tier Considerations

The design targets AWS Free Tier by:

- Keeping Lambda invocations low volume (personal project / demo traffic).
- Using DynamoDB with small item sizes and low read/write throughput.
- Serving a lightweight static frontend from S3 (optionally with CloudFront).
- Avoiding long-running compute like EC2.

## Current Status (Local Dev)

- Flask backend exposes:
  - `/health`
  - `/me`
  - `/top-artists`
  - `/top-tracks`
  - `/taste-profile` (built using `build_taste_profile()`)

- `backend/taste_profile.py`:
  - Contains the core aggregation logic that will be reused in Lambda.

- `backend/save_taste_profile_locally.py`:
  - Simulates a DynamoDB item locally by writing taste profiles to `data/` as JSON.
  - Uses the same pk/sk schema planned for DynamoDB.

Next steps will include:

1. Creating a Lambda handler that wraps `build_taste_profile()`.
2. Adding an API Gateway HTTP API that forwards `GET /taste-profile` to Lambda.
3. Creating a real DynamoDB table using the same item shape.
4. Hosting the frontend on S3 (and optionally CloudFront).

## Current Status (Week 3)

- Taste profiles are built and saved via AWS Lambda
- Profiles are persisted in DynamoDB
- Users can retrieve ranked matches using:
  - `GET /matches/{user_id}?limit=N`
- Matching logic is simple, explainable, and documented
