from __future__ import annotations

import re
from typing import Any, Dict, List, Set


def _norm(s: str) -> str:
    """
    Normalize strings so matching is consistent.

    Day 2 upgrade:
      - Normalize Unicode dashes (–, —, etc) -> "-"
      - Normalize feat variants: feat., featuring, ft., ft -> "feat"
      - Normalize spaces (including around hyphens): "a  -  b" -> "a - b"
      - Lowercase + trim
    """
    if not isinstance(s, str):
        return ""

    s = s.strip()

    # A) Normalize dash-like characters to a simple hyphen "-"
    dash_chars = [
        "\u2010",  # hyphen
        "\u2011",  # non-breaking hyphen
        "\u2012",  # figure dash
        "\u2013",  # en dash
        "\u2014",  # em dash
        "\u2212",  # minus sign
    ]
    for ch in dash_chars:
        s = s.replace(ch, "-")

    # Lowercase early so regex is simpler
    s = s.lower()

    # B) Normalize "feat" variants
    # IMPORTANT: Handle trailing dot safely (feat. / ft.)
    # We match the word boundary on the word, then optionally consume a dot.
    s = re.sub(r"\b(featuring|feat|ft)\b\.?", "feat", s)

    # C) Normalize spaces around hyphens (keeps "song - artist" stable)
    s = re.sub(r"\s*-\s*", " - ", s)

    # D) Collapse multiple spaces/tabs/newlines
    s = " ".join(s.split())

    return s


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
        "raw_score": int,           # points (not percent)
        "max_raw_score": int,       # best possible points given what each user has
        "match_score": int,         # 0-100 (percent-style score)
        "match_percent": int,       # 0-100 (same as match_score)
        "shared_artists": [...],
        "shared_genres": [...],
        "shared_tracks": [...],
        "counts": {"artists": int, "genres": int, "tracks": int},
        "weights": {"artist": 3, "genre": 2, "track": 1},

        # Day 4:
        "explain": {
          "artist_points": int,
          "genre_points": int,
          "track_points": int,
          "shared_artists_sample": [...],
          "shared_genres_sample": [...],
          "shared_tracks_sample": [...],
        }
      }
    """
    # Extract normalized sets
    a_artists = _extract_artists(profile_a)
    b_artists = _extract_artists(profile_b)

    a_genres = _extract_genres(profile_a)
    b_genres = _extract_genres(profile_b)

    a_tracks = _extract_tracks(profile_a)
    b_tracks = _extract_tracks(profile_b)

    # Shared overlap
    shared_artists = sorted(a_artists & b_artists)
    shared_genres = sorted(a_genres & b_genres)
    shared_tracks = sorted(a_tracks & b_tracks)

    # Points (raw)
    raw_score = (len(shared_artists) * 3) + (len(shared_genres) * 2) + (len(shared_tracks) * 1)

    # NEW: compute a true percent based on "max possible overlap points"
    # Use mins so we don't pretend they could share more than either user has available.
    max_raw_score = (
        (min(len(a_artists), len(b_artists)) * 3)
        + (min(len(a_genres), len(b_genres)) * 2)
        + (min(len(a_tracks), len(b_tracks)) * 1)
    )

    if max_raw_score <= 0:
        match_percent = 0
    else:
        match_percent = _cap_0_100((float(raw_score) / float(max_raw_score)) * 100.0)

    # Keep match_score aligned with the percent for UI simplicity
    match_score = int(match_percent)

    # -------------------------
    # Day 4: explain breakdown
    # -------------------------
    artist_points = len(shared_artists) * 3
    genre_points = len(shared_genres) * 2
    track_points = len(shared_tracks) * 1

    explain = {
        "artist_points": int(artist_points),
        "genre_points": int(genre_points),
        "track_points": int(track_points),
        "shared_artists_sample": shared_artists[:3],
        "shared_genres_sample": shared_genres[:3],
        "shared_tracks_sample": shared_tracks[:3],
    }

    return {
        "debug_matching_version": "week6-day4-explain-v1",
        "raw_score": int(raw_score),
        "max_raw_score": int(max_raw_score),
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
        "explain": explain,
    }
