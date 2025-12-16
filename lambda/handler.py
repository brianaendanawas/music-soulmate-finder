"""
handler.py

AWS Lambda handler for building a music taste profile.

Expected event format:

{
  "items": {
    "user_id": "spotify:user:123",
    "top_artists": [...],
    "top_genres": [...],
    "top_tracks": [...]
  }
}
"""

import json
from typing import Any, Dict

from build_taste_profile import build_taste_profile


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main AWS Lambda entry point.
    """
    # Log that we got an invocation (for CloudWatch metric filter later)
    print("TasteProfile invocation received")

    # Basic validation
    items = event.get("items")
    if items is None:
        error_body = {
            "error": "Missing 'items' in event. Expected event['items'] to contain taste data."
        }

        # Log the error too
        print("TasteProfile error: event missing 'items' key")

        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_body),
        }

    # Build the taste profile using the pure function
    profile = build_taste_profile(items)

    # Optional: log user id
    user_id = items.get("user_id", "unknown-user")
    print(f"TasteProfile built successfully for user_id={user_id}")

    # Return Lambda-style HTTP response
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(profile, ensure_ascii=False),
    }
