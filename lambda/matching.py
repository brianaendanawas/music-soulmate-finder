from __future__ import annotations

from typing import Any, Dict, Set


def _norm(s: str) -> str:
    """Normalize strings so matching is consistent."""
    return " ".join(s.strip().lower().split())


def _extract_artists(profile: Dict[str, Any]) -> Set[str]:
    """
    Your Day 3 profile stores sample artists like:
      profile["sample"]["top_artists"] = ["Artist 1", "Artist 2", ...]
    """
    artists = profile.get("sample", {}).get("top_artists", []) or []
    out: Set[str] = set()
    for a in artists:
        if isinstance(a, str) and a.strip():
            out.add(_norm(a))
    return out


def _extract_tracks(profile: Dict[str, Any]) -> Set[str]:
    """
    Your Day 3 profile stores sample tracks like:
      profile["sample"]["top_tracks"] = ["Song A – Artist 1", ...]
    """
    tracks = profile.get("sample", {}).get("top_tracks", []) or []
    out: Set[str] = set()
    for t in tracks:
        if isinstance(t, str) and t.strip():
            out.add(_norm(t))
    return out


def _extract_genres(profile: Dict[str, Any]) -> Set[str]:
    """
    Your Day 3 profile stores ranked genres like:
      profile["top_genres"] = [{"genre": "pop", "count": 2}, ...]
    """
    top_genres = profile.get("top_genres", []) or []
    out: Set[str] = set()

    for g in top_genres:
        if isinstance(g, dict):
            genre_name = g.get("genre")
            if isinstance(genre_name, str) and genre_name.strip():
                out.add(_norm(genre_name))
        elif isinstance(g, str) and g.strip():
            out.add(_norm(g))

    return out


def compute_match_score(profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      {
        "match_score": int,
        "shared_artists": [...],
        "shared_genres": [...],
        "shared_tracks": [...],
        "counts": {"artists": int, "genres": int, "tracks": int}
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

    score = (len(shared_artists) * 3) + (len(shared_genres) * 2) + (len(shared_tracks) * 1)

    return {
        "match_score": score,
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
