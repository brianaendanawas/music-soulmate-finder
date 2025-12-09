from collections import Counter
from typing import Dict, Any


def build_taste_profile(sp) -> Dict[str, Any]:
    """
    Build a simple 'taste profile' from the user's top artists and tracks.

    This function is pure Python logic that can be reused later in:
    - Flask (current project)
    - AWS Lambda handler (future serverless version)

    It expects an authenticated Spotify client 'sp'.
    """
    top_artists_data = sp.current_user_top_artists(limit=20)
    top_tracks_data = sp.current_user_top_tracks(limit=20)

    # ---- Favorite genres ----
    genre_counts = Counter()
    for artist in top_artists_data["items"]:
        for genre in artist.get("genres") or []:
            genre_counts[genre] += 1

    favorite_genres = [g for g, _ in genre_counts.most_common(5)]

    # ---- Favorite artists ----
    favorite_artists = [a.get("name") for a in top_artists_data["items"][:5]]

    # ---- Sample tracks ----
    sample_tracks = []
    for t in top_tracks_data["items"][:5]:
        artists = t.get("artists", [])
        main_artist_name = artists[0]["name"] if artists else "Unknown artist"
        sample_tracks.append(
            {"name": t.get("name"), "artist": main_artist_name}
        )

    # ---- Summary ----
    summary_parts = []

    if favorite_genres:
        summary_parts.append(
            f"You mainly listen to genres like {', '.join(favorite_genres[:3])}."
        )

    if favorite_artists:
        summary_parts.append(
            f"Your top artists include {', '.join(favorite_artists[:3])}."
        )

    summary = (
        " ".join(summary_parts)
        if summary_parts
        else "We couldn't build a taste profile yet – Spotify may need more listening data."
    )

    return {
        "favorite_genres": favorite_genres,
        "favorite_artists": favorite_artists,
        "sample_tracks": sample_tracks,
        "summary": summary,
    }
