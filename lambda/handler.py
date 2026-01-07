from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import boto3

from build_taste_profile import build_taste_profile
from matching import compute_match_score

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = (
    os.environ.get("DDB_TABLE_NAME")
    or os.environ.get("TABLE_NAME")
    or "music-soulmate-profiles"
)
table = dynamodb.Table(TABLE_NAME)

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")


def _json_response(status_code: int, body: Any) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Headers": "content-type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def _get_method_path(event: Dict[str, Any]) -> Tuple[str, str]:
    rc = event.get("requestContext", {}) or {}
    http = rc.get("http", {}) or {}
    method = (http.get("method") or event.get("httpMethod") or "").upper()
    path = http.get("path") or event.get("path") or ""
    return method, path


def _read_json_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def _get_path_param(event: Dict[str, Any], name: str) -> Optional[str]:
    params = event.get("pathParameters") or {}
    val = params.get(name)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _safe_int(val: Optional[str], default: int) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default


def _scan_all_profiles(exclude_user_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    scan_kwargs: Dict[str, Any] = {}

    while True:
        resp = table.scan(**scan_kwargs)
        for it in resp.get("Items", []):
            if it.get("user_id") != exclude_user_id:
                items.append(it)

        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    return items


def handle_post_taste_profile(event: Dict[str, Any]) -> Dict[str, Any]:
    data = _read_json_body(event)

    user_id = data.get("user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        return _json_response(400, {"error": "Missing required field: user_id"})

    profile = build_taste_profile(data)
    now = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "user_id": user_id,
            "profile": profile,
            "updated_at": now,
        }
    )

    return _json_response(200, {"message": "Profile saved", "user_id": user_id})


def handle_get_matches(event: Dict[str, Any]) -> Dict[str, Any]:
    user_id = _get_path_param(event, "user_id")
    if not user_id:
        return _json_response(400, {"error": "Missing path param: user_id"})

    qs = event.get("queryStringParameters") or {}
    limit = _safe_int(qs.get("limit") if isinstance(qs, dict) else None, 10)
    limit = max(1, min(limit, 25))

    # LOG LINE #1
    print(f"Computing matches for user_id={user_id}, limit={limit}")

    me = table.get_item(Key={"user_id": user_id}).get("Item")
    if not me:
        return _json_response(404, {"error": f"No profile found for {user_id}"})

    me_profile = me.get("profile", {})
    others = _scan_all_profiles(exclude_user_id=user_id)

    # LOG LINE #2
    print(f"Scanned {len(others)} other profiles from table={TABLE_NAME}")

    matches = []
    for it in others:
        scored = compute_match_score(me_profile, it.get("profile", {}))
        matches.append(
            {
                "user_id": it["user_id"],
                "score": scored.get("match_score", 0),
                "shared_artists": scored.get("shared_artists", []),
                "shared_genres": scored.get("shared_genres", []),
                "shared_tracks": scored.get("shared_tracks", []),
            }
        )

    matches.sort(key=lambda m: m["score"], reverse=True)

    return _json_response(
        200,
        {"for_user_id": user_id, "limit": limit, "matches": matches[:limit]},
    )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method, path = _get_method_path(event)

    if method == "OPTIONS":
        return _json_response(200, {"ok": True})

    if method == "POST" and path.endswith("/taste-profile"):
        return handle_post_taste_profile(event)

    if method == "GET" and path.startswith("/matches/"):
        if not (event.get("pathParameters") or {}).get("user_id"):
            event["pathParameters"] = {"user_id": path.split("/matches/", 1)[-1]}
        return handle_get_matches(event)

    return _json_response(404, {"error": "Route not found"})
