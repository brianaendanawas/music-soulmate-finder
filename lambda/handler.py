"""
handler.py

AWS Lambda handler for building a music taste profile.

This is designed to be used with the build_taste_profile module.
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
    # Basic validation
    items = event.get("items")
    if items is None:
        error_body = {
            "error": "Missing 'items' in event. Expected event['items'] to contain taste data."
        }
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_body),
        }

    # Build the taste profile using our pure function
    profile = build_taste_profile(items)

    # Wrap it in a standard Lambda HTTP-style response
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(profile, ensure_ascii=False),
    }
