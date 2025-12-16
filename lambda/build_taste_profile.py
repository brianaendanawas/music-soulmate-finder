"""
build_taste_profile.py

Designed for AWS Lambda: builds a simple music taste profile
from input JSON (Python dict).

This module is PURE Python:
- No Flask
- No Spotify client
- No file system access

It can be imported by a Lambda handler or tested locally.
"""

from collections import Counter
from typing import Dict, Any, List


def _safe_list(value) -> List[Any]:
    """Helper: ensure a value is always returned as a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_taste_profile(items: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a music taste profile from a simple input structure.

    Expected input format (example):

    items = {
        "user_id": "spotify:123",
        "top_artists": ["NCT 127", "Red Velvet", "NewJeans"],
        "top_genres": ["k-pop", "k-pop", "r&b", "pop"],
        "top_tracks": [
            "Track A – NCT 127",
            "Track B – Jungwoo Solo",
        ],
    }

    This function does NOT call Spotify or any external API.
    It only works with the data passed in via 'items'.
    """

    user_id = items.get("user_id", "unknown-user")

    top_artists = _safe_list(items.get("top_artists"))
    top_genres = _safe_list(items.get("top_genres"))
    top_tracks = _safe_list(items.get("top_tracks"))

    # Basic stats
    artist_count = len(top_artists)
    track_count = len(top_tracks)
    unique_genres = set(top_genres)

    # Genre ranking
    genre_counter = Counter(top_genres)
    top_genres_ranked = [
        {"genre": genre, "count": count}
        for genre, count in genre_counter.most_common(5)
    ]

    favorite_artist = top_artists[0] if top_artists else None
    favorite_genre = top_genres_ranked[0]["genre"] if top_genres_ranked else None

    profile: Dict[str, Any] = {
        "user_id": user_id,
        "summary": {
            "favorite_artist": favorite_artist,
            "favorite_genre": favorite_genre,
            "description": _build_description(
                favorite_artist=favorite_artist,
                favorite_genre=favorite_genre,
                artist_count=artist_count,
                track_count=track_count,
                genre_variety=len(unique_genres),
            ),
        },
        "stats": {
            "artist_count": artist_count,
            "track_count": track_count,
            "genre_variety": len(unique_genres),
        },
        "top_genres": top_genres_ranked,
        "sample": {
            "top_artists": top_artists[:5],
            "top_tracks": top_tracks[:5],
        },
    }

    return profile


def _build_description(
    favorite_artist: str | None,
    favorite_genre: str | None,
    artist_count: int,
    track_count: int,
    genre_variety: int,
) -> str:
    """
    Build a human-friendly description.

    Kept simple on purpose so it's easy to return from Lambda or store in DynamoDB later.
    """
    parts: List[str] = []

    if favorite_artist:
        parts.append(f"You really love {favorite_artist}.")
    if favorite_genre:
        parts.append(f"Your main genre is {favorite_genre}.")

    parts.append(f"You've got {artist_count} favorite artists and {track_count} top tracks.")
    parts.append(f"You listen across {genre_variety} different genres.")

    return " ".join(parts)
