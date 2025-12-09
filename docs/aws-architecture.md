# Music Soulmate Finder – AWS Architecture (Planned)

This project starts as a local Flask + Spotify API app, but is designed to be
migrated to a serverless AWS architecture using Free Tier–friendly services.

## High-Level Design

**Goal:** Match users based on their music taste profiles, using Spotify data.

Planned AWS components:

- **Amazon API Gateway (HTTP API)**
  - Public entrypoint for the frontend.
  - Routes:
    - `GET /taste-profile`
    - `GET /top-artists`
    - `GET /top-tracks`
    - (Later) `GET /matches`

- **AWS Lambda (Python)**
  - One function for taste profile aggregation.
  - Reuses the same logic found in `backend/taste_profile.py`.
  - Responsible for:
    - Calling Spotify with an access token
    - Building the `taste_profile` object
    - Reading/writing taste profile items in DynamoDB

- **Amazon DynamoDB**
  - Stores user taste profiles in a simple pk/sk (single-table) pattern.
  - Example item (mirrored by `backend/save_taste_profile_locally.py`):

    ```json
    {
      "pk": "USER#spotify_user_id",
      "sk": "TASTE_PROFILE#CURRENT",
      "user_id": "spotify_user_id",
      "generated_at": "2025-12-08T12:34:56Z",
      "taste_profile": {
        "favorite_genres": ["k-pop", "pop", "r&b"],
        "favorite_artists": ["NCT 127", "BLACKPINK", "The Weeknd"],
        "sample_tracks": [
          {"name": "Favorite", "artist": "NCT 127"}
        ],
        "summary": "You mainly listen to genres like k-pop, pop, r&b. Your top artists include NCT 127, BLACKPINK, The Weeknd."
      }
    }
    ```

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
