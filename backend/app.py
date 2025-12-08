from collections import Counter

from flask import Flask, jsonify, render_template
from .spotify_client import create_spotify_client


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def home():
        """
        Serve the main HTML page.
        """
        return render_template("index.html")

    @app.get("/health")
    def health_check():
        """
        Simple health check endpoint.
        """
        return jsonify({"status": "ok", "service": "music-soulmate-backend"})

    @app.get("/me")
    def get_me():
        """
        Return a simplified Spotify profile for the current user.
        """
        sp = create_spotify_client()
        user = sp.current_user()

        images = user.get("images") or []
        image_url = images[0]["url"] if images else None

        profile = {
            "id": user.get("id"),
            "display_name": user.get("display_name"),
            "spotify_url": user.get("external_urls", {}).get("spotify"),
            "image_url": image_url,
            "followers": user.get("followers", {}).get("total"),
        }

        return jsonify({"profile": profile})

    @app.get("/top-artists")
    def get_top_artists():
        """
        Return the current user's top artists as structured objects.
        """
        sp = create_spotify_client()
        results = sp.current_user_top_artists(limit=10)

        artists = []
        for a in results["items"]:
            images = a.get("images") or []
            image_url = images[0]["url"] if images else None

            artists.append(
                {
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "image_url": image_url,
                    # Spotify sometimes includes genres on artists:
                    "genres": a.get("genres") or [],
                }
            )

        return jsonify({"top_artists": artists})

    @app.get("/top-tracks")
    def get_top_tracks():
        """
        Return the current user's top tracks as structured objects.
        """
        sp = create_spotify_client()
        results = sp.current_user_top_tracks(limit=10)

        tracks = []
        for t in results["items"]:
            tracks.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "artists": [artist["name"] for artist in t.get("artists", [])],
                    "spotify_url": t.get("external_urls", {}).get("spotify"),
                    "preview_url": t.get("preview_url"),
                }
            )

        return jsonify({"top_tracks": tracks})

    @app.get("/taste-profile")
    def get_taste_profile():
        """
        Build a simple 'taste profile' from the user's top artists and tracks.
        This is shaped so it can later be stored in DynamoDB or returned by Lambda.
        """
        sp = create_spotify_client()

        # Fetch a bit more data so the summary feels richer
        top_artists_data = sp.current_user_top_artists(limit=20)
        top_tracks_data = sp.current_user_top_tracks(limit=20)

        # ---- Favorite genres (based on artists) ----
        genre_counts = Counter()
        for artist in top_artists_data["items"]:
            for genre in artist.get("genres") or []:
                genre_counts[genre] += 1

        # Take the top 5 genres
        favorite_genres = [g for g, _ in genre_counts.most_common(5)]

        # ---- Favorite artists (names) ----
        favorite_artists = [a.get("name") for a in top_artists_data["items"][:5]]

        # ---- Sample tracks (name + first artist) ----
        sample_tracks = []
        for t in top_tracks_data["items"][:5]:
            artists = t.get("artists", [])
            main_artist_name = artists[0]["name"] if artists else "Unknown artist"
            sample_tracks.append(
                {
                    "name": t.get("name"),
                    "artist": main_artist_name,
                }
            )

        # ---- Simple summary string ----
        # This is a human-readable description that will look good on a resume demo.
        summary_parts = []

        if favorite_genres:
            summary_parts.append(
                f"You mainly listen to genres like {', '.join(favorite_genres[:3])}."
            )

        if favorite_artists:
            summary_parts.append(
                f"Your top artists include {', '.join(favorite_artists[:3])}."
            )

        if not summary_parts:
            summary = "We couldn't build a taste profile yet – Spotify may need more listening data."
        else:
            summary = " ".join(summary_parts)

        taste_profile = {
            "favorite_genres": favorite_genres,
            "favorite_artists": favorite_artists,
            "sample_tracks": sample_tracks,
            "summary": summary,
        }

        return jsonify({"taste_profile": taste_profile})

    return app


# This block runs only when you call 'python -m backend.app' (or python app.py
# if this file is run directly).
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
