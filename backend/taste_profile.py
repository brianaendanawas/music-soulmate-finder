from importlib import import_module
from typing import Any, Dict


# Reuse the same pure profile builder that the AWS Lambda save-profile flow uses.
# "lambda" is a Python keyword, so import_module lets us import that package path
# without duplicating the builder logic in the Flask backend.
_build_matching_profile = import_module("lambda.build_taste_profile").build_taste_profile


def collect_spotify_profile_data(sp) -> Dict[str, Any]:
    """
    Collect real Spotify listening data in the raw shape expected by the
    AWS POST /taste-profile endpoint.

    This function does NOT build the final matching profile.
    AWS or build_taste_profile() can do that separately.
    """
    user = sp.current_user()
    top_artists_data = sp.current_user_top_artists(limit=20)
    top_tracks_data = sp.current_user_top_tracks(limit=20)

    top_artists = []
    top_genres = []
    top_tracks = []

    for artist in top_artists_data.get("items", []):
        name = artist.get("name")

        if isinstance(name, str) and name.strip():
            top_artists.append(name.strip())

        for genre in artist.get("genres") or []:
            if isinstance(genre, str) and genre.strip():
                top_genres.append(genre.strip())

    for track in top_tracks_data.get("items", []):
        name = track.get("name")

        if not isinstance(name, str) or not name.strip():
            continue

        artists = track.get("artists") or []
        main_artist = None

        if artists and isinstance(artists[0], dict):
            artist_name = artists[0].get("name")

            if isinstance(artist_name, str) and artist_name.strip():
                main_artist = artist_name.strip()

        if main_artist:
            top_tracks.append(f"{name.strip()} – {main_artist}")
        else:
            top_tracks.append(name.strip())

    return {
        "user_id": user.get("id") or "unknown-user",
        "top_artists": top_artists,
        "top_genres": top_genres,
        "top_tracks": top_tracks,
    }


def build_taste_profile(sp) -> Dict[str, Any]:
    """
    Build the canonical matching-compatible taste profile from real Spotify data.

    Spotify data is first collected in the raw shape expected by the shared
    profile builder. The same builder used by AWS then creates the canonical
    matching profile.
    """
    raw_profile = collect_spotify_profile_data(sp)
    return _build_matching_profile(raw_profile)