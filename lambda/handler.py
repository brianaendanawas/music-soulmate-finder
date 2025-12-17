"""
handler.py

AWS Lambda handler for building a music taste profile.

Supported event formats:

1) Direct invocation (used by test_lambda_locally.py and console test):

{
  "items": {
    "user_id": "spotify:user:123",
    "top_artists": [...],
    "top_genres": [...],
    "top_tracks": [...]
  }
}

2) API Gateway HTTP API (Lambda proxy integration, JSON body):

{
  "version": "2.0",
  "routeKey": "POST /taste-profile",
  "rawPath": "/taste-profile",
  "body": "{\"items\": { ... }}",
  ...
}
"""

import json
from typing import Any, Dict

from build_taste_profile import build_taste_profile


def _extract_items_from_event(event: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Try to extract the 'items' dict from either:
    - direct invocation: event["items"]
    - HTTP API event: json.loads(event["body"])["items"]
    """
    # Case 1: direct invocation from test_lambda_locally.py or Lambda console test
    if "items" in event:
        return event["items"]

    # Case 2: HTTP API event with JSON body
    body = event.get("body")
    if body is None:
        return None

    try:
        body_obj = json.loads(body)
    except json.JSONDecodeError:
        print("TasteProfile error: body is not valid JSON")
        return None

    items = body_obj.get("items")
    return items


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main AWS Lambda entry point.
    Works with both:
    - direct invocation events
    - API Gateway HTTP API events
    """
    print("TasteProfile invocation received")
    print(f"Raw event keys: {list(event.keys())}")

    items = _extract_items_from_event(event)

    if items is None:
        error_body = {
            "error": "Missing 'items' in event. Expected either event['items'] "
                     "or a JSON body with an 'items' field."
        }

        print("TasteProfile error: could not find 'items' in event")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_body),
        }

    profile = build_taste_profile(items)

    user_id = items.get("user_id", "unknown-user")
    print(f"TasteProfile built successfully for user_id={user_id}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(profile, ensure_ascii=False),
    }
