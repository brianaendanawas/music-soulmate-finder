# AWS Lambda Architecture – Music Soulmate Finder

This document explains how the **Music Soulmate Finder** project uses AWS Lambda to build a music “taste profile” that can be consumed by the frontend and (later) stored in a database.

---

## 1. High-level overview

The Lambda function is responsible for:

- Receiving a JSON payload that represents a user’s listening data  
- Transforming that data into a structured “taste profile”  
- Returning the result as JSON to API Gateway (and then to the frontend)  
- Emitting logs and metrics so the function can be monitored

The function is implemented in the repo under:

- `lambda/build_taste_profile.py`  → pure Python transformation logic  
- `lambda/handler.py`             → `lambda_handler(event, context)` entry point

---

## 2. Before vs After (Architecture)

### Before (purely local)

[Browser] --> [Flask backend] --> [Spotify API]
                   |
                   +--> /taste-profile (local Python function only)
All logic ran inside the local Flask app.

There was no AWS component.

The /taste-profile endpoint was not reachable from outside the local machine.

After (with AWS Lambda)

[Browser] --HTTP POST--> [API Gateway] --invoke--> [AWS Lambda]
                                                     |
                                                     +--> build_taste_profile(...)
                                                     |
                                                     +--> CloudWatch Logs + Metrics

Key changes:

- Taste profile logic was extracted into a reusable Python module (build_taste_profile.py).
- The logic now runs in AWS Lambda, not just on the local machine.
- API Gateway exposes a public HTTPS endpoint that any frontend can call.

3. Lambda entry point (lambda_handler)
The Lambda entry point is defined in lambda/handler.py with the standard signature:

```python
def lambda_handler(event, context):
    """
    AWS Lambda entry point for building a music taste profile.

    Expected event format (simplified):

    {
        "items": {
            "user_id": "spotify:user:briana",
            "top_artists": [...],
            "top_genres": [...],
            "top_tracks": [...]
        }
    }
    """
    # 1. Read items from event
    # 2. Call build_taste_profile(items)
    # 3. Return a JSON-serializable response
```

The core transformation logic lives in build_taste_profile.py, which can also be imported and tested locally without AWS.

This separation makes it easy to:

- Test the pure Python logic locally
- Reuse the same function in other environments if needed
- Keep the Lambda handler focused on I/O (event in, response out)

4. Sample event and response
Example request event (from API Gateway → Lambda)
The frontend sends a request body like:

```json
{
  "items": {
    "user_id": "spotify:user:briana",
    "top_artists": [
      "NCT 127",
      "Taeyeon",
      "Red Velvet",
      "NewJeans"
    ],
    "top_genres": [
      "k-pop",
      "k-pop",
      "r&b",
      "pop"
    ],
    "top_tracks": [
      "Favorite – NCT 127",
      "Sticker – NCT 127",
      "Moonlight – NCT 127",
      "Track A – Taeyeon"
    ]
  }
}
```

API Gateway passes this body (usually as a string) into event.
The Lambda handler:

1. Parses the JSON body (if needed, depending on integration type).
2. Extracts items.
3. Calls build_taste_profile(items).

Example response from Lambda
A simplified response structure:

```json
{
  "taste_profile": {
    "summary": "You listen to a lot of energetic k-pop with strong vocals.",
    "favorite_genres": ["k-pop", "r&b", "pop"],
    "favorite_artists": ["NCT 127", "Taeyeon"],
    "sample_tracks": [
      { "name": "Favorite – NCT 127", "artist": "NCT 127" },
      { "name": "Sticker – NCT 127", "artist": "NCT 127" }
    ]
  }
}
```

API Gateway then serializes this to JSON and returns it to the caller (the frontend).

5. Logging & monitoring (CloudWatch)
The Lambda function writes logs automatically to CloudWatch Logs.
During Week 2, a metric filter was added to count invocations:

- Log group: Lambda log group for this function
- Metric filter: e.g. TasteProfileInvocations
- Namespace: MusicSoulmate

This makes it possible to:

- Monitor how often the taste profile is being requested
- Build CloudWatch dashboards and, later, alarms

6. Design goals
The Lambda architecture is intentionally simple but “cloud-ready”:

- Stateless: Lambda does not store user-specific state.
- Deterministic: Given the same input items, it returns the same taste_profile.
- Composable: The build_taste_profile function can be reused by:
  - Other Lambdas
  - Local scripts
  - Future backends

This structure mirrors real-world serverless patterns and is meant to be easy to extend in future weeks (e.g. DynamoDB integration, more complex metrics, or multiple Lambda functions).