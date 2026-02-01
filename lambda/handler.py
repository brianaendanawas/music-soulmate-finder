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


def _artists_preview_from_profile(profile: Dict[str, Any], limit: int = 5) -> List[str]:
    """
    Best-effort: extract artist names from a built taste profile.
    Supports either:
      - profile["top_artists"] as list[str]
      - profile["top_artists"] as list[{"name": "..."}]
      - profile["artists"] as list[str] or list[{"name": "..."}]
    """
    for key in ("top_artists", "artists"):
        val = profile.get(key)
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, str):
                return [x for x in val if isinstance(x, str) and x][:limit]
            if isinstance(first, dict) and "name" in first:
                names = [a.get("name") for a in val if isinstance(a, dict) and a.get("name")]
                return names[:limit]
    return []


# -------------------------
# Profiles: public helpers
# -------------------------
def _extract_genres_preview(profile: Dict[str, Any], limit: int = 5) -> List[str]:
    """
    Best-effort genre extraction from the stored 'profile' map.
    Supports either:
      - profile["top_genres"] as list[str]
      - profile["genres"] as list[str]
      - profile["genre_weights"] as dict[str, number] (sorted desc)
    """
    val = profile.get("top_genres")
    if isinstance(val, list):
        return [g for g in val if isinstance(g, str) and g][:limit]

    val = profile.get("genres")
    if isinstance(val, list):
        return [g for g in val if isinstance(g, str) and g][:limit]

    weights = profile.get("genre_weights")
    if isinstance(weights, dict):
        try:
            items = sorted(
                [(k, weights[k]) for k in weights.keys() if isinstance(k, str)],
                key=lambda kv: float(kv[1]) if kv[1] is not None else 0.0,
                reverse=True,
            )
            return [k for k, _ in items[:limit]]
        except Exception:
            return []

    return []


def _public_profile_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    profile = item.get("profile") if isinstance(item.get("profile"), dict) else {}
    connections = item.get("connections")
    if not isinstance(connections, list):
        connections = []

    return {
        "user_id": item.get("user_id"),
        "display_name": item.get("display_name") or item.get("user_id"),
        "bio": item.get("bio") or "",
        "top_artists_preview": item.get("top_artists_preview") or [],
        "top_genres_preview": _extract_genres_preview(profile, limit=5),
        "connections": connections,
        "updated_at": item.get("updated_at") or "",
    }


def _profile_for_scoring(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine nested 'profile' (Day 3 taste profile) with item-level preview fields,
    so matching.py can find artists/genres/tracks no matter where they're stored.
    """
    base = item.get("profile")
    merged: Dict[str, Any] = base if isinstance(base, dict) else {}

    # Copy so we don't mutate the original
    out: Dict[str, Any] = dict(merged)

    # Item-level previews (your UI uses these)
    if isinstance(item.get("top_artists_preview"), list):
        out["top_artists_preview"] = item.get("top_artists_preview") or []

    # If you ever store genres preview at top-level, support it too
    if isinstance(item.get("top_genres_preview"), list):
        out["top_genres_preview"] = item.get("top_genres_preview") or []

    return out


def handle_post_taste_profile(event: Dict[str, Any]) -> Dict[str, Any]:
    data = _read_json_body(event)

    user_id = data.get("user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        return _json_response(400, {"error": "Missing required field: user_id"})

    profile = build_taste_profile(data)

    display_name = data.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        display_name = user_id

    bio = data.get("bio")
    if not isinstance(bio, str):
        bio = ""

    top_preview = data.get("top_artists_preview")
    if not isinstance(top_preview, list) or not all(isinstance(x, str) for x in top_preview):
        top_preview = _artists_preview_from_profile(profile, limit=5)

    now = datetime.now(timezone.utc).isoformat()

    # IMPORTANT: preserve existing "connections" if present
    existing = table.get_item(Key={"user_id": user_id}).get("Item") or {}
    connections = existing.get("connections")
    if not isinstance(connections, list):
        connections = []

    table.put_item(
        Item={
            "user_id": user_id,
            "profile": profile,
            "updated_at": now,
            "display_name": display_name,
            "bio": bio,
            "top_artists_preview": top_preview,
            "connections": connections,
        }
    )

    return _json_response(
        200,
        {
            "message": "Profile saved",
            "user_id": user_id,
            "display_name": display_name,
            "bio": bio,
            "top_artists_preview": top_preview,
            "connections": connections,
        },
    )


def handle_get_matches(event: Dict[str, Any]) -> Dict[str, Any]:
    user_id = _get_path_param(event, "user_id")
    if not user_id:
        return _json_response(400, {"error": "Missing path param: user_id"})

    qs = event.get("queryStringParameters") or {}
    limit = _safe_int(qs.get("limit") if isinstance(qs, dict) else None, 10)
    limit = max(1, min(limit, 25))

    print(f"Computing matches for user_id={user_id}, limit={limit}")

    me = table.get_item(Key={"user_id": user_id}).get("Item")
    if not me:
        return _json_response(404, {"error": f"No profile found for {user_id}"})

    me_profile = me.get("profile", {})
    me_for_scoring = _profile_for_scoring(me)

    others = _scan_all_profiles(exclude_user_id=user_id)
    print(f"Scanned {len(others)} other profiles from table={TABLE_NAME}")

    matches = []
    for it in others:
        other_for_scoring = _profile_for_scoring(it)

        scored = compute_match_score(me_for_scoring, other_for_scoring)

        shared_artists = scored.get("shared_artists", []) or []
        shared_genres = scored.get("shared_genres", []) or []

        matches.append(
            {
                "user_id": it["user_id"],
                "display_name": it.get("display_name") or it["user_id"],
                "bio": it.get("bio") or "",
                "top_artists_preview": it.get("top_artists_preview") or [],
                # Keep existing "score" for UI compatibility (now capped 0-100)
                "score": scored.get("match_score", 0),

                # NEW Day 1 fields
                "raw_score": scored.get("raw_score", scored.get("match_score", 0)),
                "match_percent": scored.get("match_percent", scored.get("match_score", 0)),

                "shared_artist_count": len(shared_artists),
                "shared_artists": shared_artists,

                # ✅ Day 3 addition (additive, safe)
                "shared_genre_count": len(shared_genres),
                "shared_genres": shared_genres,

                "shared_tracks": scored.get("shared_tracks", []) or [],
            }
        )

    matches.sort(key=lambda m: m["score"], reverse=True)

    return _json_response(
        200,
        {
            "debug": {
                "matches_handler_version": "week5-day7-verify-v1",
                "table": TABLE_NAME,
                "me_profile_keys": sorted(list(me_profile.keys())) if isinstance(me_profile, dict) else [],
                "me_top_artists_preview_count": len(me.get("top_artists_preview") or []),
            },
            "for_user_id": user_id,
            "limit": limit,
            "matches": matches[:limit],
        },
    )


def handle_get_profile(event: Dict[str, Any]) -> Dict[str, Any]:
    user_id = _get_path_param(event, "user_id")
    if not user_id:
        return _json_response(400, {"error": "Missing path param: user_id"})

    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    if not item:
        return _json_response(404, {"error": f"User not found: {user_id}"})

    return _json_response(200, _public_profile_from_item(item))


# -------------------------
# NEW: Connections
# POST /connect
# -------------------------
def _get_body_user_ids(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Accept flexible payload keys:
      - from_user_id / to_user_id
      - user_id / target_user_id
    """
    from_id = data.get("from_user_id") or data.get("user_id")
    to_id = data.get("to_user_id") or data.get("target_user_id")
    if isinstance(from_id, str):
        from_id = from_id.strip()
    else:
        from_id = None
    if isinstance(to_id, str):
        to_id = to_id.strip()
    else:
        to_id = None
    return from_id, to_id


def handle_post_connect(event: Dict[str, Any]) -> Dict[str, Any]:
    data = _read_json_body(event)
    from_user_id, to_user_id = _get_body_user_ids(data)

    if not from_user_id or not to_user_id:
        return _json_response(
            400,
            {
                "error": "Missing required fields",
                "expected": {
                    "from_user_id": "briana_test_003",
                    "to_user_id": "briana_test_002",
                },
            },
        )

    if from_user_id == to_user_id:
        return _json_response(400, {"error": "Cannot connect to yourself"})

    # Ensure both users exist
    from_item = table.get_item(Key={"user_id": from_user_id}).get("Item")
    if not from_item:
        return _json_response(404, {"error": f"from_user_id not found: {from_user_id}"})

    to_item = table.get_item(Key={"user_id": to_user_id}).get("Item")
    if not to_item:
        return _json_response(404, {"error": f"to_user_id not found: {to_user_id}"})

    # Read existing connections to avoid duplicates
    existing = from_item.get("connections")
    if not isinstance(existing, list):
        existing = []

    if to_user_id in existing:
        return _json_response(
            200,
            {
                "message": "Already connected",
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "connections": existing,
            },
        )

    now = datetime.now(timezone.utc).isoformat()
    new_connections = existing + [to_user_id]

    # Update only the needed fields
    table.update_item(
        Key={"user_id": from_user_id},
        UpdateExpression="SET connections = :c, updated_at = :u",
        ExpressionAttributeValues={
            ":c": new_connections,
            ":u": now,
        },
    )

    return _json_response(
        200,
        {
            "message": "Connected",
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "connections": new_connections,
            "updated_at": now,
        },
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

    if method == "GET" and path.startswith("/profiles/"):
        if not (event.get("pathParameters") or {}).get("user_id"):
            event["pathParameters"] = {"user_id": path.split("/profiles/", 1)[-1]}
        return handle_get_profile(event)

    # NEW: POST /connect
    if method == "POST" and (path.endswith("/connect") or path == "/connect"):
        return handle_post_connect(event)

    return _json_response(404, {"error": "Route not found"})
