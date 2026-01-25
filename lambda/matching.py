from __future__ import annotations

from typing import Any, Dict, List, Set


def _norm(s: str) -> str:
    """Normalize strings so matching is consistent."""
    return " ".join(s.strip().lower().split())


def _strings_from_list(val: Any) -> List[str]:
    """
    Accepts:
      - ["a", "b"]
      - [{"name": "a"}, {"name": "b"}]
      - None
    Returns: list[str]
    """
    if not isinstance(val, list) or not val:
        return []
    out: List[str] = []
    for x in val:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
        elif isinstance(x, dict):
            name = x.get("name")
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
    return out


def _get_nested(profile: Dict[str, Any], *keys: str) -> Any:
    cur: Any = profile
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _extract_artists(profile: Dict[str, Any]) -> Set[str]:
    """
    Supports multiple shapes:
      Day 3: profile["sample"]["top_artists"] = [...]
      Older/other: profile["top_artists"] / profile["favorite_artists"] / profile["artists"] = [...]
      UI preview: profile["top_artists_preview"] = [...]
    """
    candidates: List[str] = []

    # Day 3
    candidates += _strings_from_list(_get_nested(profile, "sample", "top_artists"))

    # Other common fields
    candidates += _strings_from_list(profile.get("favorite_artists"))
    candidates += _strings_from_list(profile.get("top_artists"))
    candidates += _strings_from_list(profile.get("artists"))

    # Preview field (stored at the DynamoDB item level sometimes, but safe here too)
    candidates += _strings_from_list(profile.get("top_artists_preview"))

    out: Set[str] = set()
    for a in candidates:
        if isinstance(a, str) and a.strip():
            out.add(_norm(a))
    return out


def _extract_tracks(profile: Dict[str, Any]) -> Set[str]:
    """
    Supports:
      Day 3: profile["sample"]["top_tracks"] = ["Song – Artist", ...]
      Other: profile["top_tracks"] / profile["tracks"] = [...]
    """
    candidates: List[str] = []
    candidates += _strings_from_list(_get_nested(profile, "sample", "top_tracks"))
    candidates += _strings_from_list(profile.get("top_tracks"))
    candidates += _strings_from_list(profile.get("tracks"))

    out: Set[str] = set()
    for t in candidates:
        if isinstance(t, str) and t.strip():
            out.add(_norm(t))
    return out


def _extract_genres(profile: Dict[str, Any]) -> Set[str]:
    """
    Supports:
      Day 3: profile["top_genres"] = [{"genre": "pop", "count": 2}, ...]
      Older: profile["top_genres"] = ["pop", "k-pop"]
      Other: profile["genres"] = ["pop", ...]
      Preview: profile["top_genres_preview"] = ["pop", ...]
      Weights: profile["genre_weights"] = {"pop": 3, ...}
    """
    out: Set[str] = set()

    # Day 3 / Older: top_genres list
    top_genres = profile.get("top_genres") or []
    if isinstance(top_genres, list):
        for g in top_genres:
            if isinstance(g, dict):
                name = g.get("genre")
                if isinstance(name, str) and name.strip():
                    out.add(_norm(name))
            elif isinstance(g, str) and g.strip():
                out.add(_norm(g))

    # Other fields
    genres = profile.get("genres") or []
    if isinstance(genres, list):
        for g in genres:
            if isinstance(g, str) and g.strip():
                out.add(_norm(g))

    preview = profile.get("top_genres_preview") or []
    if isinstance(preview, list):
        for g in preview:
            if isinstance(g, str) and g.strip():
                out.add(_norm(g))

    weights = profile.get("genre_weights")
    if isinstance(weights, dict):
        for k in weights.keys():
            if isinstance(k, str) and k.strip():
                out.add(_norm(k))

    return out


def _cap_0_100(x: float) -> int:
    """Cap a score to [0, 100] and return as int."""
    if x < 0:
        return 0
    if x > 100:
        return 100
    return int(x)


def compute_match_score(profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      {
        "raw_score": int,
        "match_score": int,        # capped 0-100
        "match_percent": int,      # 0-100 int (same scale as match_score)
        "shared_artists": [...],
        "shared_genres": [...],
        "shared_tracks": [...],
        "counts": {"artists": int, "genres": int, "tracks": int},
        "weights": {"artist": 3, "genre": 2, "track": 1},
      }
    """
    a_artists = _extract_artists(profile_a)
    b_artists = _extract_artists(profile_b)

    a_genres = _extract_genres(profile_a)
    b_genres = _extract_genres(profile_b)

    a_tracks = _extract_tracks(profile_a)
    b_tracks = _extract_tracks(profile_b)

    shared_artists = sorted(a_artists & b_artists)
    shared_genres = sorted(a_genres & b_genres)
    shared_tracks = sorted(a_tracks & b_tracks)

    # Same simple weighting as before (keep it explainable)
    raw_score = (len(shared_artists) * 3) + (len(shared_genres) * 2) + (len(shared_tracks) * 1)

    # Day 1 change: cap to 0-100 for a stable UI-friendly score
    match_score = _cap_0_100(float(raw_score))

    # Keep percent as a clean 0-100 integer (same as capped score)
    match_percent = int(round(match_score))

    return {
        "debug_matching_version": "week6-day1-scorecap-v1",
        "raw_score": int(raw_score),
        "match_score": int(match_score),
        "match_percent": int(match_percent),
        "shared_artists": shared_artists,
        "shared_genres": shared_genres,
        "shared_tracks": shared_tracks,
        "counts": {
            "artists": len(shared_artists),
            "genres": len(shared_genres),
            "tracks": len(shared_tracks),
        },
        "weights": {"artist": 3, "genre": 2, "track": 1},
    }
