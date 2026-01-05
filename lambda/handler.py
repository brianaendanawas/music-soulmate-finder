from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Dict, Tuple

from build_taste_profile import build_taste_profile
from profile_store import save_profile


def _json_safe(value: Any) -> Any:
    """Convert Decimal (from DynamoDB) into int/float so json.dumps works."""
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _parse_event(event: Dict[str, Any]) -> Tuple[str, Any]:
    """
    Supports:
    1) Direct Lambda test event
    2) API Gateway HTTP API (proxy integration)
    """
    if "body" in event and event["body"] is not None:
        body = event["body"]
        if isinstance(body, str):
            payload = json.loads(body)
        elif isinstance(body, dict):
            payload = body
        else:
            raise ValueError("Unsupported body type")
    else:
        payload = event

    user_id = payload.get("user_id") or payload.get("userId")
    items = payload.get("items")

    if not user_id:
        raise ValueError("Missing required field: user_id")
    if not isinstance(items, list):
        raise ValueError("Missing or invalid required field: items (must be a list)")

    return user_id, items


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        user_id, items = _parse_event(event)

        # 1) Build taste profile
        profile = build_taste_profile(items)
        profile["user_id"] = user_id


        # 2) Save to DynamoDB
        save_profile(user_id=user_id, profile=profile)

        print(f"Profile saved for user_id={user_id}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "ok": True,
                "user_id": user_id,
                "profile": _json_safe(profile),
            }),
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")

        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"ok": False, "error": str(e)}),
        }
